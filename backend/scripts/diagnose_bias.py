"""Read-only diagnostic: why is the day-ahead wind error a large systematic bias?

Builds decision and naive frames for all 31 delivery days (cutoff 09:00) with the
existing service functions, then prints labelled sections of evidence.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import httpx
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.forecast_selection import (  # noqa: E402
    expand_hourly_to_half_hourly,
    select_decision_forecast,
    select_naive_forecast,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
LONDON = "Europe/London"
DELIVERY_START = dt.date(2026, 1, 2)
DELIVERY_END = dt.date(2026, 2, 1)
SAMPLE_DAY = dt.date(2026, 1, 15)
CUTOFF = dt.time(9, 0)

# (name, lo, hi) — left-closed, right-open
HORIZON_BUCKETS: list[tuple[str, float, float]] = [
    ("(-inf,-12)", float("-inf"), -12.0),
    ("[-12,-6)", -12.0, -6.0),
    ("[-6,0)", -6.0, 0.0),
    ("[0,6)", 0.0, 6.0),
    ("[6,12)", 6.0, 12.0),
    ("[12,24)", 12.0, 24.0),
    ("[24,36)", 24.0, 36.0),
    ("[36,48)", 36.0, 48.0),
    ("[48,inf)", 48.0, float("inf")),
]

ACTUAL_BINS: list[tuple[str, float, float]] = [
    ("[0,3000)", 0.0, 3000.0),
    ("[3000,6000)", 3000.0, 6000.0),
    ("[6000,9000)", 6000.0, 9000.0),
    ("[9000,12000)", 9000.0, 12000.0),
    ("[12000,15000)", 12000.0, 15000.0),
    ("[15000,inf)", 15000.0, float("inf")),
]


def delivery_days() -> list[dt.date]:
    return [
        DELIVERY_START + dt.timedelta(days=i)
        for i in range((DELIVERY_END - DELIVERY_START).days + 1)
    ]


def build_frames(
    expanded: pd.DataFrame, actuals: pd.DataFrame
) -> tuple[list[pd.DataFrame], list[pd.DataFrame]]:
    decision, naive = [], []
    for day in delivery_days():
        sel = select_decision_forecast(expanded, day, CUTOFF)
        sel = sel.merge(actuals[["start_time", "actual_mw"]], on="start_time", how="left")
        sel["delivery_date"] = day
        nv = select_naive_forecast(expanded, day)
        nv = nv.merge(actuals[["start_time", "actual_mw"]], on="start_time", how="left")
        nv["delivery_date"] = day
        decision.append(sel)
        naive.append(nv)
    return decision, naive


def _stats(forecast: pd.Series, actual: pd.Series) -> str:
    valid = pd.concat([forecast, actual], axis=1, keys=["f", "a"]).dropna()
    err = valid["f"] - valid["a"]
    corr = valid["f"].corr(valid["a"])
    return (
        f"n={len(valid)} mean_actual={valid['a'].mean():8.1f} "
        f"mean_forecast={valid['f'].mean():8.1f} "
        f"ratio_fcst_over_actual={valid['f'].mean() / valid['a'].mean():.3f} "
        f"bias={err.mean():7.1f} mae={err.abs().mean():7.1f} corr={corr:.3f}"
    )


def section_levels(decision: list[pd.DataFrame], naive: list[pd.DataFrame]) -> None:
    print("=== 1. LEVELS ===")
    for label, frames in (("decision", decision), ("naive", naive)):
        rows = pd.concat(frames, ignore_index=True)
        print(f"{label:>8}: {_stats(rows['forecast_mw'], rows['actual_mw'])}")


def section_by_horizon_including_negative(expanded: pd.DataFrame, actuals: pd.DataFrame) -> None:
    print("=== 2. BY HORIZON INCLUDING NEGATIVE (all expanded rows with actual) ===")
    window = (expanded["start_time"] >= pd.Timestamp(f"{DELIVERY_START}T00:00Z")) & (
        expanded["start_time"] < pd.Timestamp(f"{DELIVERY_END + dt.timedelta(days=1)}T00:00Z")
    )
    rows = expanded[window].merge(
        actuals[["start_time", "actual_mw"]], on="start_time", how="inner"
    )
    rows = rows[rows["forecast_mw"].notna()]
    rows = rows.assign(
        horizon_hours=(rows["start_time"] - rows["publish_time"]).dt.total_seconds() / 3600
    )
    print(f"total joined rows: {len(rows)}")
    for name, lo, hi in HORIZON_BUCKETS:
        bucket = rows[(rows["horizon_hours"] >= lo) & (rows["horizon_hours"] < hi)]
        if bucket.empty:
            continue
        err = bucket["forecast_mw"] - bucket["actual_mw"]
        print(
            f"{name:>10}: n={len(bucket)} mean_err={err.mean():7.1f} "
            f"mae={err.abs().mean():7.1f} "
            f"mean_actual={bucket['actual_mw'].mean():8.1f} "
            f"mean_forecast={bucket['forecast_mw'].mean():8.1f}"
        )


def _shift_table(rows: pd.DataFrame, offsets: list[int], step_minutes: int) -> None:
    rows = rows.sort_values("start_time").reset_index(drop=True)
    series = pd.concat([rows["forecast_mw"], rows["actual_mw"]], axis=1, keys=["f", "a"])
    for k in offsets:
        valid = pd.concat([series["f"].shift(k), series["a"]], axis=1, keys=["f", "a"]).dropna()
        err = valid["f"] - valid["a"]
        corr = valid["f"].corr(valid["a"])
        print(
            f"k={k:+d} ({k * step_minutes:+d} min): n={len(valid)} "
            f"bias={err.mean():7.1f} mae={err.abs().mean():7.1f} corr={corr:.3f}"
        )


def section_shift_test(decision: list[pd.DataFrame], naive: list[pd.DataFrame]) -> None:
    print("=== 3. TIME SHIFT TEST (forecast column shifted by k rows of 30 min) ===")
    for label, frames in (("decision", decision), ("naive", naive)):
        chunks = [f[f["start_time"].dt.minute == 0].copy() for f in frames] if False else frames
        rows = pd.concat(chunks, ignore_index=True)
        print(f"-- {label}, half-hourly, k in -6..+6 --")
        _shift_table(rows, list(range(-6, 7)), 30)
    print("-- hourly-only :00 slots, shifts in whole hours --")
    for label, frames in (("decision", decision), ("naive", naive)):
        hourly = [f[f["start_time"].dt.minute == 0].copy() for f in frames]
        rows = pd.concat(hourly, ignore_index=True)
        print(f"-- {label}, k in -6..+6 rows (30-min grid = +/-3 h on hourly grid) --")
        _shift_table(rows, list(range(-6, 7)), 30)


def section_by_actual_level(decision: list[pd.DataFrame]) -> None:
    print("=== 4. BIAS BY ACTUAL LEVEL (decision frames) ===")
    rows = pd.concat(decision, ignore_index=True).dropna(subset=["actual_mw"])
    for name, lo, hi in ACTUAL_BINS:
        bucket = rows[(rows["actual_mw"] >= lo) & (rows["actual_mw"] < hi)]
        if bucket.empty:
            continue
        err = bucket["forecast_mw"] - bucket["actual_mw"]
        print(
            f"{name:>12}: n={len(bucket)} mean_err={err.mean():7.1f} "
            f"mae={err.abs().mean():7.1f} "
            f"mean_actual={bucket['actual_mw'].mean():8.1f} "
            f"mean_forecast={bucket['forecast_mw'].mean():8.1f}"
        )


def section_by_london_hour(decision: list[pd.DataFrame]) -> None:
    print("=== 5. BIAS BY LONDON HOUR OF DAY (decision frames) ===")
    rows = pd.concat(decision, ignore_index=True).dropna(subset=["actual_mw"])
    rows = rows.assign(hour=rows["start_time"].dt.tz_convert(LONDON).dt.hour)
    for hour in range(24):
        bucket = rows[rows["hour"] == hour]
        err = bucket["forecast_mw"] - bucket["actual_mw"]
        print(
            f"hour={hour:02d}: n={len(bucket)} mean_err={err.mean():7.1f} mae={err.abs().mean():7.1f}"
        )


def section_by_delivery_day(decision: list[pd.DataFrame]) -> None:
    print("=== 6. BIAS BY DELIVERY DAY (decision frames) ===")
    positive_days = []
    for frame in decision:
        day = frame["delivery_date"].iloc[0]
        err = (frame["forecast_mw"] - frame["actual_mw"]).dropna()
        mean_actual = float(frame["actual_mw"].mean())
        mean_forecast = float(frame["forecast_mw"].mean())
        print(
            f"{day}: n={len(err)} mean_actual={mean_actual:8.1f} "
            f"mean_forecast={mean_forecast:8.1f} mean_err={err.mean():7.1f}"
        )
        if err.mean() > 0:
            positive_days.append(day)
    print(f"days with positive mean error: {len(positive_days)} of {len(decision)}")


def section_sample_day(decision: list[pd.DataFrame], naive: list[pd.DataFrame]) -> None:
    print(f"=== 7. SAMPLE DAY {SAMPLE_DAY} ===")
    dec = next(f for f in decision if f["delivery_date"].iloc[0] == SAMPLE_DAY)
    nv = next(f for f in naive if f["delivery_date"].iloc[0] == SAMPLE_DAY)
    merged = (
        dec[["start_time", "actual_mw", "forecast_mw", "publish_time"]]
        .rename(columns={"forecast_mw": "dec_forecast"})
        .merge(
            nv[["start_time", "forecast_mw"]].rename(columns={"forecast_mw": "naive_forecast"}),
            on="start_time",
            how="left",
        )
    )
    for _, row in merged.iterrows():
        print(
            f"{row['start_time']} actual={row['actual_mw']!s:>8} "
            f"dec_fcst={row['dec_forecast']!s:>8} naive_fcst={row['naive_forecast']!s:>8} "
            f"dec_publish={row['publish_time']}"
        )


def section_fuelhh_scope() -> None:
    print(f"=== 8. RAW FUELHH SCOPE CHECK ({SAMPLE_DAY}, no fuelType filter) ===")
    url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream"
    response = httpx.get(
        url,
        params={
            "settlementDateFrom": SAMPLE_DAY.isoformat(),
            "settlementDateTo": SAMPLE_DAY.isoformat(),
        },
        timeout=60,
    )
    response.raise_for_status()
    rows = pd.DataFrame(response.json())
    rows["startTime"] = pd.to_datetime(rows["startTime"], utc=True)
    print("distinct fuelType values:", sorted(rows["fuelType"].unique()))
    slot = rows[rows["startTime"] == pd.Timestamp(f"{SAMPLE_DAY}T12:00:00Z")]
    print("per fuelType at 2026-01-15T12:00Z:")
    for _, row in slot.sort_values("fuelType").iterrows():
        print(f"  {row['fuelType']:>12}: {row['generation']:>10.1f} MW")
    wind_named = [f for f in rows["fuelType"].unique() if "WIND" in str(f).upper() and f != "WIND"]
    print("other fuelType names containing 'WIND':", wind_named or "none")


def section_windfor_semantics(forecasts_raw: pd.DataFrame) -> None:
    actuals = pd.read_parquet(DATA_DIR / "actuals.parquet")
    print(f"=== 9. RAW WINDFOR SEMANTICS (slot {SAMPLE_DAY}T12:00Z, non-expanded) ===")
    slot_actual = actuals[
        (actuals["start_time"] >= pd.Timestamp(f"{SAMPLE_DAY}T12:00:00Z"))
        & (actuals["start_time"] <= pd.Timestamp(f"{SAMPLE_DAY}T12:30:00Z"))
    ].sort_values("start_time")
    print(
        "actual_mw: 12:00Z =",
        float(slot_actual["actual_mw"].iloc[0]),
        "| 12:30Z =",
        float(slot_actual["actual_mw"].iloc[1]),
    )
    rows = forecasts_raw[
        forecasts_raw["start_time"] == pd.Timestamp(f"{SAMPLE_DAY}T12:00:00Z")
    ].sort_values("publish_time")
    print("forecast rows for start_time 12:00Z (sorted by publish_time):")
    for _, row in rows.iterrows():
        horizon = (row["start_time"] - row["publish_time"]).total_seconds() / 3600
        print(
            f"  publish={row['publish_time']} "
            f"forecast_mw={float(row['forecast_mw']):8.1f} horizon_h={horizon:+.1f}"
        )
    print("naive selection keeps the LAST row above (publish far after the slot).")


def main() -> None:
    actuals = pd.read_parquet(DATA_DIR / "actuals.parquet")
    raw = pd.read_parquet(DATA_DIR / "forecasts.parquet")
    expanded = expand_hourly_to_half_hourly(raw)
    decision, naive = build_frames(expanded, actuals)

    section_levels(decision, naive)
    section_by_horizon_including_negative(expanded, actuals)
    section_shift_test(decision, naive)
    section_by_actual_level(decision)
    section_by_london_hour(decision)
    section_by_delivery_day(decision)
    section_sample_day(decision, naive)
    section_fuelhh_scope()
    section_windfor_semantics(raw)


if __name__ == "__main__":
    main()
