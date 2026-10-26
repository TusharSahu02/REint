import { useSearchParams } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type {
  AccuracyByDay,
  AccuracyOverall,
  Basis,
  HistogramBin,
  HourEntry,
} from '../api/types'
import { apiBase } from '../api/client'
import DataQualityBanner from '../components/DataQualityBanner'
import { useAccuracy, useAppConfig } from '../hooks/useApi'

const num = (v: number | null | undefined): string =>
  v == null ? '–' : v.toLocaleString('en-GB', { maximumFractionDigits: 1 })

const dayFmt = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Europe/London',
  day: '2-digit',
  month: 'short',
})

const binLabel = (b: HistogramBin): string => `${Math.round(b.bin_start_mw)}..${Math.round(b.bin_end_mw)}`

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="kpi">
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  )
}

function OverallKpis({ m, caption }: { m: AccuracyOverall; caption: string }) {
  return (
    <section className="card">
      <h2>{caption}</h2>
      <div className="kpis">
        <Kpi label="Valid slots (n)" value={num(m.n)} />
        <Kpi label="MAE (MW)" value={num(m.mae_mw)} />
        <Kpi label="RMSE (MW)" value={num(m.rmse_mw)} />
        <Kpi label="Bias, mean error (MW)" value={num(m.bias_mw)} />
        <Kpi label="nMAE (% of mean actual)" value={m.nmae_pct == null ? '–' : `${num(m.nmae_pct)}%`} />
        <Kpi label="P90 |error| (MW)" value={num(m.p90_abs_error_mw)} />
        <Kpi label="P95 |error| (MW)" value={num(m.p95_abs_error_mw)} />
      </div>
    </section>
  )
}

export default function Accuracy() {
  const [params, setParams] = useSearchParams()
  const config = useAppConfig()
  const cfg = config.data

  const start = params.get('start') ?? cfg?.delivery_start ?? ''
  const end = params.get('end') ?? cfg?.delivery_end ?? ''
  const basis: Basis = params.get('basis') === 'all_horizons' ? 'all_horizons' : 'decision'
  const cutoff = params.get('cutoff') ?? cfg?.cutoff_local_time ?? null

  const dateOk = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(start) && /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(end)
  const rangeOk = Boolean(cfg && dateOk && start >= cfg.delivery_start && end <= cfg.delivery_end && start <= end)
  const enabled = rangeOk

  const accuracy = useAccuracy(start, end, basis, cutoff, enabled)

  const setParam = (key: 'start' | 'end' | 'basis' | 'cutoff', value: string | null) => {
    setParams((prev) => {
      if (value) prev.set(key, value)
      else prev.delete(key)
      return prev
    })
  }

  const data = accuracy.data
  const hist = (data?.error_histogram ?? []).map((b) => ({ label: binLabel(b), count: b.count }))
  const byHour = (data?.by_hour_of_day ?? []).map((h: HourEntry) => ({
    hour: h.hour,
    mae: h.mae_mw,
    bias: h.bias_mw,
  }))
  const byHorizon = (data?.by_horizon ?? []).map((h) => ({
    bucket: h.horizon_bucket_hours,
    mae: h.mae_mw,
    bias: h.bias_mw,
  }))
  const byDay: AccuracyByDay[] = data?.by_day ?? []

  return (
    <>
      <section className="controls card">
        <label>
          From (delivery day)
          <input
            type="date"
            value={start}
            min={cfg?.delivery_start}
            max={cfg?.delivery_end}
            onChange={(e) => setParam('start', e.target.value)}
            disabled={!cfg}
          />
        </label>
        <label>
          To (delivery day)
          <input
            type="date"
            value={end}
            min={cfg?.delivery_start}
            max={cfg?.delivery_end}
            onChange={(e) => setParam('end', e.target.value)}
            disabled={!cfg}
          />
        </label>
        <label>
          Basis
          <select value={basis} onChange={(e) => setParam('basis', e.target.value)}>
            <option value="decision">Decision-time forecast</option>
            <option value="all_horizons">All horizons</option>
          </select>
        </label>
      </section>

      {config.isError && (
        <div className="banner" role="status">
          Backend unreachable at {apiBase}. Start it with: uvicorn app.main:app --port 8000
        </div>
      )}
      {dateOk && !rangeOk && cfg && (
        <div className="banner" role="status">
          Range {start}–{end} is outside the supported range {cfg.delivery_start}–{cfg.delivery_end}.
        </div>
      )}

      {accuracy.isPending && enabled && <p>Loading…</p>}
      {accuracy.isError && <p className="error">Failed to load: {accuracy.error.message}</p>}

      {data && (
        <>
          <OverallKpis m={data.overall} caption={`Accuracy — decision-time basis, ${data.range.start} to ${data.range.end}`} />
          {data.overall.n_missing_forecast + data.overall.n_missing_actual > 0 && (
            <DataQualityBanner
              nMissingForecast={data.overall.n_missing_forecast}
              nMissingActual={data.overall.n_missing_actual}
            />
          )}

          {data.basis === 'decision' && data.naive_overall && (
            <section className="card naive">
              <h2>Leakage check — decision-time vs naive (no cutoff)</h2>
              <table>
                <thead>
                  <tr>
                    <th>Basis</th>
                    <th>MAE (MW)</th>
                    <th>Bias (MW)</th>
                    <th>nMAE (% mean actual)</th>
                    <th>P90 |error| (MW)</th>
                    <th>n</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Decision-time (usable)</td>
                    <td>{num(data.overall.mae_mw)}</td>
                    <td>{num(data.overall.bias_mw)}</td>
                    <td>{data.overall.nmae_pct == null ? '–' : num(data.overall.nmae_pct)}</td>
                    <td>{num(data.overall.p90_abs_error_mw)}</td>
                    <td>{num(data.overall.n)}</td>
                  </tr>
                  <tr>
                    <td>Naive (not usable)</td>
                    <td>{num(data.naive_overall.mae_mw)}</td>
                    <td>{num(data.naive_overall.bias_mw)}</td>
                    <td>{data.naive_overall.nmae_pct == null ? '–' : num(data.naive_overall.nmae_pct)}</td>
                    <td>{num(data.naive_overall.p90_abs_error_mw)}</td>
                    <td>{num(data.naive_overall.n)}</td>
                  </tr>
                </tbody>
              </table>
              <p className="muted">
                Naive numbers look better because they use forecasts the buyer did not yet have.
              </p>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={byDay} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="delivery_date" tickFormatter={(d: string) => dayFmt.format(new Date(d))} tick={{ fontSize: 11 }} />
                  <YAxis width={64} tick={{ fontSize: 12 }} tickFormatter={(v: number) => v.toLocaleString('en-GB')} />
                  <Tooltip labelFormatter={(d) => String(d)} />
                  <Legend />
                  <Bar dataKey="mae_mw" name="Decision MAE (MW)" fill="#2563eb" />
                  <Bar dataKey="naive_mae_mw" name="Naive MAE (MW)" fill="#93c5fd" />
                </BarChart>
              </ResponsiveContainer>
            </section>
          )}

          <section className="card">
            <h2>Forecast vs actual over the range</h2>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={data.timeseries} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="start_time"
                  tickFormatter={(t: string) => dayFmt.format(new Date(t))}
                  minTickGap={64}
                  tick={{ fontSize: 11 }}
                />
                <YAxis width={64} tick={{ fontSize: 12 }} tickFormatter={(v: number) => v.toLocaleString('en-GB')} />
                <Tooltip
                  labelFormatter={(t) => String(t).slice(0, 16).replace('T', ' ') + 'Z'}
                  formatter={(v: unknown, n: unknown) => [num(typeof v === "number" ? v : null) + " MW", String(n)]}
                />
                <Legend />
                <Line type="linear" dataKey="forecast_mw" name="Forecast (MW)" stroke="#2563eb" dot={false} connectNulls={false} />
                <Line type="linear" dataKey="actual_mw" name="Actual (MW)" stroke="#b45309" dot={false} connectNulls={false} />
              </LineChart>
            </ResponsiveContainer>
          </section>

          <section className="card">
            <h2>Error distribution (MW)</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={hist} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={4} angle={-45} textAnchor="end" height={70} />
                <YAxis width={48} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" name="Half-hours" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
            <p className="muted">Error = forecast − actual; positive bins = over-forecast (buyer under-buys).</p>
          </section>

          <section className="card">
            <h2>Error by hour of day (Europe/London)</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byHour} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                <YAxis width={64} tick={{ fontSize: 12 }} tickFormatter={(v: number) => v.toLocaleString('en-GB')} />
                <Tooltip formatter={(v: unknown, n: unknown) => [num(typeof v === "number" ? v : null) + " MW", String(n)]} />
                <Legend />
                <Bar dataKey="mae" name="MAE (MW)" fill="#2563eb" />
                <Bar dataKey="bias" name="Bias (MW)" fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          </section>

          <section className="card">
            <h2>Error by forecast horizon (all forecasts, any basis)</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byHorizon} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
                <YAxis width={64} tick={{ fontSize: 12 }} tickFormatter={(v: number) => v.toLocaleString('en-GB')} />
                <Tooltip formatter={(v: unknown, n: unknown) => [num(typeof v === "number" ? v : null) + " MW", String(n)]} />
                <Legend />
                <Bar dataKey="mae" name="MAE (MW)" fill="#2563eb" />
                <Bar dataKey="bias" name="Bias (MW)" fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          </section>
        </>
      )}
    </>
  )
}
