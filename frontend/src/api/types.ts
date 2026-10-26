export type Flag = 'missing_forecast' | 'missing_actual'

export interface DecisionRow {
  start_time: string
  forecast_mw: number | null
  publish_time: string | null
  horizon_hours: number | null
  actual_mw: number | null
  error_mw: number | null
  flags: Flag[]
}

export interface DecisionSummary {
  latest_publish_time_used: string | null
  n_slots: number
  n_missing_forecast: number
  n_missing_actual: number
  mae_mw: number | null
  rmse_mw: number | null
  bias_mw: number | null
  suggested_buffer_mw: number | null
  buffer_basis: 'expanding_window' | 'full_period_fallback' | null
  buffer_sample_size: number
}

export interface DecisionForecastResponse {
  delivery_date: string
  cutoff_utc: string
  cutoff_local: string
  rows: DecisionRow[]
  summary: DecisionSummary
}

export interface AppConfig {
  cutoff_local_time: string
  timezone: string
  decision_start: string
  decision_end: string
  delivery_start: string
  delivery_end: string
}

export type Basis = 'decision' | 'all_horizons'

export interface AccuracyOverall {
  n: number
  mae_mw: number | null
  rmse_mw: number | null
  bias_mw: number | null
  nmae_pct: number | null
  p50_abs_error_mw: number | null
  p90_abs_error_mw: number | null
  p95_abs_error_mw: number | null
  n_missing_forecast: number
  n_missing_actual: number
}

export interface AccuracyByDay {
  delivery_date: string
  mae_mw: number | null
  naive_mae_mw: number | null
  bias_mw: number | null
  n: number
}

export interface TimeseriesPoint {
  start_time: string
  forecast_mw: number | null
  actual_mw: number | null
}

export interface HistogramBin {
  bin_start_mw: number
  bin_end_mw: number
  count: number
}

export interface HourEntry {
  hour: number
  mae_mw: number | null
  bias_mw: number | null
  n: number
}

export interface HorizonEntry {
  horizon_bucket_hours: string
  mae_mw: number | null
  bias_mw: number | null
  n: number
}

export interface AccuracyResponse {
  range: { start: string; end: string }
  basis: Basis
  overall: AccuracyOverall
  naive_overall: AccuracyOverall | null
  by_day: AccuracyByDay[]
  timeseries: TimeseriesPoint[]
  error_histogram: HistogramBin[]
  by_hour_of_day: HourEntry[]
  by_horizon: HorizonEntry[]
}
