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
