# API Spec (v1)

Base path: `/api`. All timestamps ISO 8601 UTC with `Z`. Generation values in MW.

## GET /api/health
`{ "status": "ok", "data_range": {"start": "...", "end": "..."}, "counts": {"actuals": n, "forecasts": n} }`

## GET /api/config
Returns defaults for the UI:
```json
{ "cutoff_local_time": "09:00", "timezone": "Europe/London",
  "decision_start": "2026-01-01", "decision_end": "2026-01-31",
  "delivery_start": "2026-01-02", "delivery_end": "2026-02-01" }
```

## GET /api/decision-forecast
Query: `date` (delivery day, YYYY-MM-DD, required), `cutoff` (HH:mm local, optional).
```json
{
  "delivery_date": "2026-01-15",
  "cutoff_utc": "2026-01-14T09:00:00Z",
  "cutoff_local": "2026-01-14T09:00:00+00:00",
  "rows": [
    { "start_time": "...Z", "forecast_mw": 5230.0, "publish_time": "...Z",
      "horizon_hours": 17.5, "actual_mw": 5011.0, "error_mw": 219.0,
      "flags": [] }
  ],
  "summary": {
    "latest_publish_time_used": "...Z",
    "n_slots": 48, "n_missing_forecast": 0, "n_missing_actual": 0,
    "mae_mw": 0, "rmse_mw": 0, "bias_mw": 0,
    "suggested_buffer_mw": 0, "buffer_basis": "expanding_window|full_period_fallback",
    "buffer_sample_size": 0
  }
}
```
`flags` values: `missing_forecast`, `missing_actual`.

## GET /api/accuracy
Query: `start`, `end` (delivery dates), `basis` = `decision` | `all_horizons` (default `decision`), `cutoff` optional.
```json
{
  "range": {"start": "...", "end": "..."},
  "basis": "decision",
  "overall": { "n": 0, "mae_mw": 0, "rmse_mw": 0, "bias_mw": 0, "nmae_pct": 0,
               "p50_abs_error_mw": 0, "p90_abs_error_mw": 0, "p95_abs_error_mw": 0,
               "n_missing_forecast": 0, "n_missing_actual": 0 },
  "naive_overall": { "...": "same shape as overall; forecast = latest publishTime ever, ignores cutoff; comparison only" },
  "by_day": [ { "delivery_date": "2026-01-15", "mae_mw": 0, "naive_mae_mw": 0, "bias_mw": 0, "n": 0 } ],
  "timeseries": [ { "start_time": "...Z", "forecast_mw": 0, "actual_mw": 0 } ],
  "error_histogram": [ { "bin_start_mw": -2000, "bin_end_mw": -1800, "count": 0 } ],
  "by_hour_of_day": [ { "hour": 0, "mae_mw": 0, "bias_mw": 0, "n": 0 } ],
  "by_horizon": [ { "horizon_bucket_hours": "0-6", "mae_mw": 0, "bias_mw": 0, "n": 0 } ]
}
```
`by_horizon` always uses all forecasts regardless of `basis`. `naive_overall` and `by_day.naive_mae_mw` are only returned when `basis=decision`.

## POST /api/refresh (optional, token-protected via `REFRESH_TOKEN` env)
Re-fetches from Elexon and reloads memory. Returns counts.

## Errors
`400` bad params (out of range date, bad cutoff), `404` no data for date, `500` unexpected. Body: `{ "detail": "..." }`.
