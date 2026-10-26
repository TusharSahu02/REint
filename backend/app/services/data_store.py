from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from app.services.forecast_selection import expand_hourly_to_half_hourly

_actuals_file = "actuals.parquet"
_forecasts_file = "forecasts.parquet"


class DataNotLoadedError(RuntimeError):
    """Raised when the store is used before the app lifespan has loaded the data."""


@dataclass
class DataStore:
    actuals: pd.DataFrame
    forecasts: pd.DataFrame  # expanded to half-hourly
    forecast_rows_raw: int  # rows in forecasts.parquet before expansion
    data_start: date
    data_end: date

    def info(self) -> dict[str, dict[str, int | str]]:
        return {
            "counts": {"actuals": int(len(self.actuals)), "forecasts": self.forecast_rows_raw},
            "data_range": {"start": self.data_start.isoformat(), "end": self.data_end.isoformat()},
        }


_store: DataStore | None = None


def _require_utc(series: pd.Series, name: str, file: Path) -> None:
    if not pd.api.types.is_datetime64_any_dtype(series):
        raise ValueError(f"{file}: column {name} is not a datetime type")
    naive = series.dt.tz is None if hasattr(series.dt, "tz") else True
    if naive:
        raise ValueError(f"{file}: column {name} is not timezone-aware UTC")


def load_data(data_dir: str) -> DataStore:
    """Load the committed snapshot and expand forecasts to half-hourly. Fails loudly."""
    root = Path(__file__).resolve().parent.parent.parent  # backend/
    base = Path(data_dir)
    base = base if base.is_absolute() else root / base

    actuals_path = base / _actuals_file
    forecasts_path = base / _forecasts_file
    for path in (actuals_path, forecasts_path):
        if not path.is_file():
            raise FileNotFoundError(f"missing data file: {path}")
    actuals = pd.read_parquet(actuals_path)
    forecasts = pd.read_parquet(forecasts_path)
    for col in ("start_time",):
        _require_utc(actuals[col], col, actuals_path)
    for col in ("start_time", "publish_time"):
        _require_utc(forecasts[col], col, forecasts_path)

    actuals = actuals.sort_values("start_time").reset_index(drop=True)
    forecasts = forecasts.sort_values(["publish_time", "start_time"]).reset_index(drop=True)
    expanded = expand_hourly_to_half_hourly(forecasts)
    start = actuals["start_time"].min().date()
    end = actuals["start_time"].max().date()
    return DataStore(
        actuals=actuals,
        forecasts=expanded,
        forecast_rows_raw=len(forecasts),
        data_start=start,
        data_end=end,
    )


def init(data_dir: str) -> DataStore:
    """Load once at startup (called from the FastAPI lifespan)."""
    global _store
    _store = load_data(data_dir)
    return _store


def get() -> DataStore:
    if _store is None:
        raise DataNotLoadedError("data store not loaded: app lifespan did not run")
    return _store
