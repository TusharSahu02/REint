from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from app.config import get_settings
from app.services import data_store
from app.services.forecast_selection import select_decision_forecast, select_naive_forecast


def _join_actual(df: pd.DataFrame, delivery_date: date) -> pd.DataFrame:
    store = data_store.get()
    out = df.merge(
        store.actuals[["start_time", "actual_mw"]],
        on="start_time",
        how="left",
        validate="one_to_one",
    )
    out["error_mw"] = out["forecast_mw"] - out["actual_mw"]
    out["delivery_date"] = out["start_time"].dt.date
    return out


@lru_cache(maxsize=256)
def decision_frame(delivery_date: date, cutoff_local: time) -> pd.DataFrame:
    """One row per half-hour slot of the delivery day, decision forecasts joined to actuals."""
    store = data_store.get()
    sel = select_decision_forecast(store.forecasts, delivery_date, cutoff_local)
    return _join_actual(sel, delivery_date)


@lru_cache(maxsize=256)
def naive_frame(delivery_date: date) -> pd.DataFrame:
    """One row per half-hour slot, naive (leaky) forecasts joined to actuals. Comparison only."""
    store = data_store.get()
    sel = select_naive_forecast(store.forecasts, delivery_date)
    return _join_actual(sel, delivery_date)


def all_horizon_frame(start_date: date, end_date: date) -> pd.DataFrame:
    """All forecast rows with a non-negative horizon and both forecast and actual present.

    Window: [local midnight of start_date, local midnight of end_date + 1 day), Europe/London.
    """
    store = data_store.get()
    zone = ZoneInfo(get_settings().timezone)
    lo = pd.Timestamp(
        datetime.combine(start_date, time(0, 0), tzinfo=zone).astimezone(timezone.utc)
    )
    hi = pd.Timestamp(
        datetime.combine(end_date + timedelta(days=1), time(0, 0), tzinfo=zone).astimezone(
            timezone.utc
        )
    )
    f = store.forecasts.merge(
        store.actuals[["start_time", "actual_mw"]], on="start_time", how="inner"
    )
    f = f[(f["start_time"] >= lo) & (f["start_time"] < hi)]
    f = f.assign(
        horizon_hours=(f["start_time"] - f["publish_time"]).dt.total_seconds() / 3600,
        error_mw=f["forecast_mw"] - f["actual_mw"],
    )
    f = f[f["horizon_hours"] >= 0].reset_index(drop=True)
    return f


def to_json_safe(obj: Any) -> Any:
    """Recursively make obj JSON-strict: NaN/NaT/inf -> None, numpy scalars -> python, ts -> ISO Z."""
    if obj is None or obj is pd.NaT:
        return None
    if isinstance(obj, dict):
        return {str(k): to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, np.ndarray)):
        return [to_json_safe(v) for v in obj]
    if isinstance(obj, (pd.Timestamp, datetime)):
        ts = pd.Timestamp(obj) if not isinstance(obj, pd.Timestamp) else obj
        if ts.tzinfo is not None:
            ts = ts.tz_convert("UTC")
        return ts.isoformat().replace("+00:00", "Z")
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        return f if math.isfinite(f) else None
    if isinstance(obj, str):
        return obj
    return obj
