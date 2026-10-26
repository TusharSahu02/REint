from __future__ import annotations

from pydantic import BaseModel


class DataRange(BaseModel):
    start: str
    end: str


class Counts(BaseModel):
    actuals: int
    forecasts: int


class HealthResponse(BaseModel):
    status: str
    data_range: DataRange
    counts: Counts


class ConfigResponse(BaseModel):
    cutoff_local_time: str
    timezone: str
    decision_start: str
    decision_end: str
    delivery_start: str
    delivery_end: str


class DecisionForecastRow(BaseModel):
    start_time: str | None
    forecast_mw: float | None
    publish_time: str | None
    horizon_hours: float | None
    actual_mw: float | None
    error_mw: float | None
    flags: list[str]


class DecisionSummary(BaseModel):
    latest_publish_time_used: str | None
    n_slots: int
    n_missing_forecast: int
    n_missing_actual: int
    mae_mw: float | None
    rmse_mw: float | None
    bias_mw: float | None
    suggested_buffer_mw: float | None
    buffer_basis: str
    buffer_sample_size: int


class DecisionForecastResponse(BaseModel):
    delivery_date: str
    cutoff_utc: str
    cutoff_local: str
    rows: list[DecisionForecastRow]
    summary: DecisionSummary


class Metrics(BaseModel):
    n: int
    mae_mw: float | None
    rmse_mw: float | None
    bias_mw: float | None
    nmae_pct: float | None
    p50_abs_error_mw: float | None
    p90_abs_error_mw: float | None
    p95_abs_error_mw: float | None
    n_missing_forecast: int
    n_missing_actual: int


class ByDayEntry(BaseModel):
    delivery_date: str
    mae_mw: float | None
    naive_mae_mw: float | None
    bias_mw: float | None
    n: int


class TimeseriesPoint(BaseModel):
    start_time: str
    forecast_mw: float | None
    actual_mw: float | None


class HistogramBin(BaseModel):
    bin_start_mw: float
    bin_end_mw: float
    count: int


class HourEntry(BaseModel):
    hour: int
    mae_mw: float | None
    bias_mw: float | None
    n: int


class HorizonEntry(BaseModel):
    horizon_bucket_hours: str
    mae_mw: float | None
    bias_mw: float | None
    n: int


class AccuracyResponse(BaseModel):
    range: DataRange
    basis: str
    overall: Metrics
    naive_overall: Metrics | None
    by_day: list[ByDayEntry]
    timeseries: list[TimeseriesPoint]
    error_histogram: list[HistogramBin]
    by_hour_of_day: list[HourEntry]
    by_horizon: list[HorizonEntry]
