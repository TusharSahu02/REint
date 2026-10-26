from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.models.schemas import (
    AccuracyResponse,
    ConfigResponse,
    DecisionForecastResponse,
    HealthResponse,
)
from app.services import data_store, frames
from app.services.buffer import over_forecast_buffer
from app.services.forecast_selection import cutoff_utc_for
from app.services.metrics import summarize

router = APIRouter(prefix="/api")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CUTOFF_RE = re.compile(r"^\d{2}:\d{2}$")

HORIZON_BUCKETS = ("0-6", "6-12", "12-24", "24-36", "36-48", "48+")


def _parse_date(value: str, query_name: str) -> date:
    if not _DATE_RE.match(value):
        raise HTTPException(status_code=400, detail=f"{query_name} must be a YYYY-MM-DD date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"{query_name} must be a YYYY-MM-DD date"
        ) from exc


def _parse_cutoff(value: str | None) -> time:
    settings = get_settings()
    if value is None:
        return time.fromisoformat(settings.decision_cutoff_local_time)
    if not _CUTOFF_RE.match(value):
        raise HTTPException(status_code=400, detail="cutoff must be a HH:mm local time")
    hour, minute = (int(part) for part in value.split(":"))
    if hour > 23 or minute > 59:
        raise HTTPException(status_code=400, detail="cutoff must be a HH:mm local time 00:00-23:59")
    return time(hour, minute)


def _check_delivery_date(day: date) -> None:
    settings = get_settings()
    if not (settings.delivery_start <= day <= settings.delivery_end):
        raise HTTPException(
            status_code=400,
            detail=(
                f"date must be a delivery day between {settings.delivery_start.isoformat()} "
                f"and {settings.delivery_end.isoformat()}"
            ),
        )


def _cutoff_strings(delivery_date: date, cutoff_local: time) -> tuple[str, str]:
    settings = get_settings()
    local = datetime.combine(
        delivery_date - timedelta(days=1), cutoff_local, ZoneInfo(settings.timezone)
    )
    cutoff_utc = cutoff_utc_for(delivery_date, cutoff_local, settings.timezone)
    cutoff_local_str = local.isoformat()
    cutoff_utc_str = cutoff_utc.isoformat().replace("+00:00", "Z")
    return cutoff_local_str, cutoff_utc_str


def _histogram_bins(errors: pd.Series) -> list[dict[str, float | int]]:
    valid = errors.dropna()
    if valid.empty or float(valid.max()) == float(valid.min()):
        return []
    counts, edges = np.histogram(valid, bins=20)
    return [
        {
            "bin_start_mw": float(edges[i]),
            "bin_end_mw": float(edges[i + 1]),
            "count": int(counts[i]),
        }
        for i in range(len(counts))
    ]


def _by_hour_of_day(rows: pd.DataFrame, tz: str) -> list[dict[str, float | int | None]]:
    zone = ZoneInfo(tz)
    present = rows.dropna(subset=["forecast_mw", "actual_mw"]).copy()
    present["error_mw"] = present["forecast_mw"] - present["actual_mw"]
    present["abs_error_mw"] = present["error_mw"].abs()
    present["hour"] = present["start_time"].dt.tz_convert(zone).dt.hour
    agg = present.groupby("hour").agg(
        mae_mw=("abs_error_mw", "mean"), bias_mw=("error_mw", "mean"), n=("error_mw", "size")
    )
    by_hour = {int(hour): agg.loc[hour].to_dict() for hour in agg.index}
    return [
        {
            "hour": hour,
            **by_hour.get(hour, {"mae_mw": None, "bias_mw": None, "n": 0}),
        }
        for hour in range(24)
    ]


def _by_horizon(horizon_rows: pd.DataFrame) -> list[dict[str, float | int | str]]:
    edges = (0, 6, 12, 24, 36, 48)
    limits = {name: (edges[i], edges[i + 1]) for i, name in enumerate(HORIZON_BUCKETS[:-1])}
    valid = horizon_rows.dropna(subset=["error_mw"])
    out: list[dict[str, float | int | str]] = []
    for name in HORIZON_BUCKETS:
        if name == "48+":
            sel = valid[valid["horizon_hours"] >= 48]
        else:
            lo, hi = limits[name]
            sel = valid[(valid["horizon_hours"] >= lo) & (valid["horizon_hours"] < hi)]
        if sel.empty:
            continue
        out.append(
            {
                "horizon_bucket_hours": name,
                "mae_mw": float(sel["error_mw"].abs().mean()),
                "bias_mw": float(sel["error_mw"].mean()),
                "n": int(len(sel)),
            }
        )
    return out


def _expanding_window_errors(day: date, cutoff_local: time) -> pd.Series:
    """Errors from decision frames for delivery days before `day` (delivery_start .. day-1)."""
    settings = get_settings()
    parts: list[pd.Series] = []
    current = settings.delivery_start
    while current < day:
        parts.append(frames.decision_frame(current, cutoff_local)["error_mw"])
        current += timedelta(days=1)
    if not parts:
        return pd.Series(dtype=float)
    return pd.concat(parts, ignore_index=True)


@router.get("/health", response_model=HealthResponse)
def health() -> dict[str, str | dict[str, str | int]]:
    store = data_store.get()
    info = store.info()
    return {"status": "ok", **info}


@router.get("/config", response_model=ConfigResponse)
def config() -> dict[str, str]:
    settings = get_settings()
    return {
        "cutoff_local_time": settings.decision_cutoff_local_time,
        "timezone": settings.timezone,
        "decision_start": settings.decision_start.isoformat(),
        "decision_end": settings.decision_end.isoformat(),
        "delivery_start": settings.delivery_start.isoformat(),
        "delivery_end": settings.delivery_end.isoformat(),
    }


@router.get("/decision-forecast", response_model=DecisionForecastResponse)
def decision_forecast(
    date: str = Query(...),  # noqa: A002  (API parameter name from the spec)
    cutoff: str | None = Query(None),
) -> dict[str, object]:
    settings = get_settings()
    delivery_day = _parse_date(date, "date")
    _check_delivery_date(delivery_day)
    cutoff_local = _parse_cutoff(cutoff)
    cutoff_local_str, cutoff_utc_str = _cutoff_strings(delivery_day, cutoff_local)

    df = frames.decision_frame(delivery_day, cutoff_local)
    has_data = bool(df["forecast_mw"].notna().any() or df["actual_mw"].notna().any())
    if not has_data:
        raise HTTPException(status_code=404, detail=f"no data for delivery day {date}")

    rows = []
    for record in df.to_dict(orient="records"):
        flags = []
        if bool(record["missing_forecast"]):
            flags.append("missing_forecast")
        if pd.isna(record["actual_mw"]):
            flags.append("missing_actual")
        rows.append(
            {
                "start_time": record["start_time"],
                "forecast_mw": record["forecast_mw"],
                "publish_time": record["publish_time"],
                "horizon_hours": record["horizon_hours"],
                "actual_mw": record["actual_mw"],
                "error_mw": record["error_mw"],
                "flags": flags,
            }
        )

    summary = summarize(df)
    latest_publish = df["publish_time"].max()

    prior_errors = _expanding_window_errors(delivery_day, cutoff_local)
    buffer_mw, sample_size = over_forecast_buffer(prior_errors)
    if buffer_mw is None:
        fallback_errors = _expanding_window_errors(
            settings.delivery_end + timedelta(days=1), cutoff_local
        )
        fallback_mw, fallback_count = over_forecast_buffer(fallback_errors)
        buffer_basis = "full_period_fallback"
        if fallback_mw is not None:
            buffer_mw, sample_size = fallback_mw, fallback_count
        else:
            buffer_mw, sample_size = None, 0
    else:
        buffer_basis = "expanding_window"

    return frames.to_json_safe(
        {
            "delivery_date": delivery_day.isoformat(),
            "cutoff_utc": cutoff_utc_str,
            "cutoff_local": cutoff_local_str,
            "rows": rows,
            "summary": {
                "latest_publish_time_used": None if pd.isna(latest_publish) else latest_publish,
                "n_slots": int(len(df)),
                "n_missing_forecast": int(df["missing_forecast"].sum()),
                "n_missing_actual": int(df["actual_mw"].isna().sum()),
                "mae_mw": summary["mae_mw"],
                "rmse_mw": summary["rmse_mw"],
                "bias_mw": summary["bias_mw"],
                "suggested_buffer_mw": buffer_mw,
                "buffer_basis": buffer_basis,
                "buffer_sample_size": int(sample_size),
            },
        }
    )


@router.get("/accuracy", response_model=AccuracyResponse)
def accuracy(
    start: str | None = Query(None),
    end: str | None = Query(None),
    basis: str = "decision",
    cutoff: str | None = Query(None),
) -> dict[str, object]:
    settings = get_settings()
    start_day = _parse_date(start, "start") if start else settings.delivery_start
    end_day = _parse_date(end, "end") if end else settings.delivery_end
    _check_delivery_date(start_day)
    _check_delivery_date(end_day)
    if start_day > end_day:
        raise HTTPException(status_code=400, detail="start must be before or equal to end")
    if basis not in ("decision", "all_horizons"):
        raise HTTPException(status_code=400, detail="basis must be decision or all_horizons")
    cutoff_local = _parse_cutoff(cutoff)

    days = [start_day + timedelta(days=i) for i in range((end_day - start_day).days + 1)]
    decision_dfs = [frames.decision_frame(day, cutoff_local) for day in days]
    naive_dfs = [frames.naive_frame(day) for day in days]
    decision_all = pd.concat(decision_dfs, ignore_index=True)
    naive_all = pd.concat(naive_dfs, ignore_index=True)

    has_data = bool(
        decision_all["forecast_mw"].notna().any() or decision_all["actual_mw"].notna().any()
    )
    if not has_data:
        raise HTTPException(status_code=404, detail="no data for the requested range")

    horizon_rows = frames.all_horizon_frame(start_day, end_day)
    if basis == "decision":
        source_rows = decision_all
        naive_overall: dict[str, object] | None = summarize(naive_all)
    else:
        source_rows = horizon_rows
        naive_overall = None
    overall = summarize(source_rows)

    by_day = []
    for day, day_df, naive_df in zip(days, decision_dfs, naive_dfs, strict=True):
        day_summary = summarize(day_df)
        by_day.append(
            {
                "delivery_date": day.isoformat(),
                "mae_mw": day_summary["mae_mw"],
                "naive_mae_mw": summarize(naive_df)["mae_mw"] if basis == "decision" else None,
                "bias_mw": day_summary["bias_mw"],
                "n": day_summary["n"],
            }
        )

    timeseries = [
        {
            "start_time": record["start_time"],
            "forecast_mw": record["forecast_mw"],
            "actual_mw": record["actual_mw"],
        }
        for record in decision_all.to_dict(orient="records")
    ]

    response = {
        "range": {"start": start_day.isoformat(), "end": end_day.isoformat()},
        "basis": basis,
        "overall": overall,
        "naive_overall": naive_overall,
        "by_day": by_day,
        "timeseries": timeseries,
        "error_histogram": _histogram_bins(source_rows["forecast_mw"] - source_rows["actual_mw"]),
        "by_hour_of_day": _by_hour_of_day(source_rows, settings.timezone),
        "by_horizon": _by_horizon(horizon_rows),
    }
    return frames.to_json_safe(response)
