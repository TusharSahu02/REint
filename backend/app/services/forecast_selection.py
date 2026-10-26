from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

DEFAULT_TZ = "Europe/London"


def expand_hourly_to_half_hourly(forecasts: pd.DataFrame) -> pd.DataFrame:
    """Step-hold: an hourly forecast covers both half-hour slots of its hour."""
    if (forecasts["start_time"].dt.minute != 0).any():
        raise ValueError("expected hourly forecasts (start_time on the hour)")
    second = forecasts.copy()
    second["start_time"] = second["start_time"] + pd.Timedelta(minutes=30)
    return pd.concat([forecasts, second], ignore_index=True)


def cutoff_utc_for(delivery_date: date, cutoff_local: time, tz: str = DEFAULT_TZ) -> datetime:
    """Cutoff = D-1 at cutoff_local in local time, converted to UTC."""
    local = datetime.combine(delivery_date - timedelta(days=1), cutoff_local, tzinfo=ZoneInfo(tz))
    return local.astimezone(timezone.utc)


def expected_slots(delivery_date: date, tz: str = DEFAULT_TZ) -> pd.DatetimeIndex:
    """All 30-minute slot start times (UTC) for the local delivery day."""
    zone = ZoneInfo(tz)
    start = datetime.combine(delivery_date, time(0, 0), tzinfo=zone).astimezone(timezone.utc)
    end = datetime.combine(delivery_date + timedelta(days=1), time(0, 0), tzinfo=zone).astimezone(
        timezone.utc
    )
    return pd.date_range(start=start, end=end, freq="30min", inclusive="left")


def _select_latest(
    forecasts: pd.DataFrame, slots: pd.DatetimeIndex, cutoff: datetime | None
) -> pd.DataFrame:
    """Latest publish_time per slot, optionally restricted to publish_time <= cutoff.

    forecasts columns: start_time (UTC), publish_time (UTC), forecast_mw. Must be half-hourly
    (already expanded).
    """
    eligible = forecasts[forecasts["start_time"].isin(slots)]
    if cutoff is not None:
        eligible = eligible[eligible["publish_time"] <= cutoff]
    chosen = (
        eligible.sort_values(["start_time", "publish_time"])
        .drop_duplicates(subset="start_time", keep="last")
        .set_index("start_time")
    )
    out = chosen.reindex(slots)
    out.index.name = "start_time"
    out["missing_forecast"] = out["forecast_mw"].isna()
    out["horizon_hours"] = (out.index.to_series() - out["publish_time"]).dt.total_seconds() / 3600
    return out.reset_index()


def select_decision_forecast(
    forecasts: pd.DataFrame,
    delivery_date: date,
    cutoff_local: time,
    tz: str = DEFAULT_TZ,
) -> pd.DataFrame:
    """Forecast the buyer actually had: latest publish_time <= cutoff, no look-ahead."""
    cutoff = cutoff_utc_for(delivery_date, cutoff_local, tz)
    return _select_latest(forecasts, expected_slots(delivery_date, tz), cutoff)


def select_naive_forecast(
    forecasts: pd.DataFrame, delivery_date: date, tz: str = DEFAULT_TZ
) -> pd.DataFrame:
    """Comparison only: latest forecast ever published, ignoring the cutoff (uses leaked info)."""
    return _select_latest(forecasts, expected_slots(delivery_date, tz), None)
