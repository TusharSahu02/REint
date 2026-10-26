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
  Basis,
  HistogramBin,
  HourEntry,
} from '../api/types'
import { apiBase } from '../api/client'
import DataQualityBanner from '../components/DataQualityBanner'
import { SkeletonPanel, SkeletonRows, SkeletonStats, SkeletonStatus } from '../components/Skeleton'
import { useAccuracy, useAppConfig } from '../hooks/useApi'
import { fmtDay, useTimezone } from '../tz'

const num = (v: number | null | undefined): string =>
  v == null ? '–' : v.toLocaleString('en-GB', { maximumFractionDigits: 1 })

const binLabel = (b: HistogramBin): string => `${Math.round(b.bin_start_mw)}..${Math.round(b.bin_end_mw)}`

function Stat({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="stat">
      <div className="stat-value">
        {value}
        {unit && <small>{unit}</small>}
      </div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

export default function Accuracy() {
  const [params, setParams] = useSearchParams()
  const config = useAppConfig()
  const cfg = config.data
  const tz = useTimezone()

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
      <div className="page-head">
        <h1>Accuracy</h1>
        <span className="provenance">
          Elexon national wind, error = forecast − actual, positive = over-forecast.
        </span>
      </div>

      <section className="toolbar">
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

      {accuracy.isPending && enabled && (
        <>
          <SkeletonStatus label="Loading accuracy" />
          <div className="section-head">
            <h2>Overall</h2>
          </div>
          <SkeletonStats n={7} />
          <div className="section-head">
            <h2>Cutoff effect</h2>
          </div>
          <SkeletonRows rows={3} cols={6} />
          <div className="section-head">
            <h2>Forecast vs actual over the range</h2>
          </div>
          <SkeletonPanel h={320} />
          <div className="section-head">
            <h2>Error distribution</h2>
          </div>
          <SkeletonPanel h={260} />
          <div className="section-head">
            <h2>Error by hour of day</h2>
          </div>
          <SkeletonPanel h={260} />
          <div className="section-head">
            <h2>Error by forecast horizon</h2>
          </div>
          <SkeletonPanel h={260} />
        </>
      )}
      {accuracy.isError && <p className="error">Failed to load: {accuracy.error.message}</p>}

      {data && (
        <>
          <div className="section-head">
            <h2>Overall, {data.range.start} to {data.range.end}</h2>
            <span className="muted">basis: {data.basis === 'decision' ? 'decision-time' : 'all horizons'}</span>
          </div>
          <section className="stats">
            <Stat label="Valid slots" value={num(data.overall.n)} />
            <Stat label="MAE" value={num(data.overall.mae_mw)} unit="MW" />
            <Stat label="RMSE" value={num(data.overall.rmse_mw)} unit="MW" />
            <Stat label="Bias" value={num(data.overall.bias_mw)} unit="MW" />
            <Stat label="nMAE" value={data.overall.nmae_pct == null ? '–' : `${num(data.overall.nmae_pct)}`} unit="%" />
            <Stat label="P90 abs error" value={num(data.overall.p90_abs_error_mw)} unit="MW" />
            <Stat label="P95 abs error" value={num(data.overall.p95_abs_error_mw)} unit="MW" />
          </section>

          {data.overall.n_missing_forecast + data.overall.n_missing_actual > 0 && (
            <DataQualityBanner
              nMissingForecast={data.overall.n_missing_forecast}
              nMissingActual={data.overall.n_missing_actual}
            />
          )}

          {data.basis === 'decision' && data.naive_overall && (
            <>
              <div className="section-head">
                <h2>Cutoff effect</h2>
                <span className="muted">decision-time vs naive (latest forecast ever published)</span>
              </div>
              <section className="section-body">
                <table>
                  <thead>
                    <tr>
                      <th>Basis</th>
                      <th className="n">MAE MW</th>
                      <th className="n">Bias MW</th>
                      <th className="n">nMAE %</th>
                      <th className="n">P90 abs err MW</th>
                      <th className="n">n</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>
                        Decision-time{' '}
                        <span className="pill usable">usable</span>
                      </td>
                      <td className="n">{num(data.overall.mae_mw)}</td>
                      <td className="n">{num(data.overall.bias_mw)}</td>
                      <td className="n">{data.overall.nmae_pct == null ? '–' : num(data.overall.nmae_pct)}</td>
                      <td className="n">{num(data.overall.p90_abs_error_mw)}</td>
                      <td className="n">{num(data.overall.n)}</td>
                    </tr>
                    <tr>
                      <td>
                        Naive <span className="pill not-usable">not usable</span>
                      </td>
                      <td className="n">{num(data.naive_overall.mae_mw)}</td>
                      <td className="n">{num(data.naive_overall.bias_mw)}</td>
                      <td className="n">{data.naive_overall.nmae_pct == null ? '–' : num(data.naive_overall.nmae_pct)}</td>
                      <td className="n">{num(data.naive_overall.p90_abs_error_mw)}</td>
                      <td className="n">{num(data.naive_overall.n)}</td>
                    </tr>
                  </tbody>
                </table>
                <p className="caption">
                  Naive numbers look better because they use forecasts the buyer did not yet have. Known
                  from day one: 31 delivery days, 48 half-hour slots each.
                </p>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={byDay} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.9 0.013 245)" vertical={false} />
                    <XAxis dataKey="delivery_date" tickFormatter={(d: string) => fmtDay(d, 'Europe/London')} tick={{ fontSize: 11 }} stroke="oklch(0.5 0.026 252)" />
                    <YAxis width={64} tick={{ fontSize: 12 }} stroke="oklch(0.5 0.026 252)" tickFormatter={(v: number) => v.toLocaleString('en-GB')} />
                    <Tooltip labelFormatter={(d) => String(d)} separator="· " />
                    <Legend />
                    <Bar dataKey="mae_mw" name="Decision MAE (MW)" fill="oklch(0.55 0.11 240)" />
                    <Bar dataKey="naive_mae_mw" name="Naive MAE (MW)" fill="oklch(0.72 0.022 250)" />
                  </BarChart>
                </ResponsiveContainer>
              </section>
            </>
          )}

          <div className="section-head">
            <h2>Forecast vs actual over the range</h2>
            <span className="muted">half-hourly, {data.basis === 'decision' ? 'decision-time forecast' : 'every published forecast'}</span>
          </div>
          <section className="section-body">
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={data.timeseries} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.9 0.013 245)" vertical={false} />
                <XAxis
                  dataKey="start_time"
                  tickFormatter={(t: string) => fmtDay(t, tz)}
                  minTickGap={64}
                  tick={{ fontSize: 11 }}
                  stroke="oklch(0.5 0.026 252)"
                />
                <YAxis width={64} tick={{ fontSize: 12 }} stroke="oklch(0.5 0.026 252)" tickFormatter={(v: number) => v.toLocaleString('en-GB')} />
                <Tooltip
                  labelFormatter={(t) => String(t).slice(0, 16).replace('T', ' ') + 'Z'}
                  formatter={(v: unknown, n: unknown) => [num(typeof v === "number" ? v : null) + " MW", String(n)]}
                  separator="· "
                />
                <Legend />
                <Line type="linear" dataKey="forecast_mw" name="Forecast (MW)" stroke="oklch(0.55 0.11 240)" dot={false} connectNulls={false} />
                <Line type="linear" dataKey="actual_mw" name="Actual (MW)" stroke="oklch(0.63 0.13 65)" dot={false} connectNulls={false} />
              </LineChart>
            </ResponsiveContainer>
          </section>

          <div className="section-head">
            <h2>Error distribution</h2>
            <span className="muted">MW, over-forecast = under-buy</span>
          </div>
          <section className="section-body">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={hist} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.9 0.013 245)" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={4} angle={-45} textAnchor="end" height={70} stroke="oklch(0.5 0.026 252)" />
                <YAxis width={48} tick={{ fontSize: 12 }} stroke="oklch(0.5 0.026 252)" />
                <Tooltip separator="· " />
                <Bar dataKey="count" name="Half-hours" fill="oklch(0.55 0.11 240)" />
              </BarChart>
            </ResponsiveContainer>
            <p className="caption">Error = forecast − actual; positive bins = over-forecast (buyer under-buys).</p>
          </section>

          <div className="section-head">
            <h2>Error by hour of day</h2>
            <span className="muted">Europe/London, decision-time basis</span>
          </div>
          <section className="section-body">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byHour} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.9 0.013 245)" vertical={false} />
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} stroke="oklch(0.5 0.026 252)" />
                <YAxis width={64} tick={{ fontSize: 12 }} stroke="oklch(0.5 0.026 252)" tickFormatter={(v: number) => v.toLocaleString('en-GB')} />
                <Tooltip formatter={(v: unknown, n: unknown) => [num(typeof v === "number" ? v : null) + " MW", String(n)]} separator="· " />
                <Legend />
                <Bar dataKey="mae" name="MAE (MW)" fill="oklch(0.78 0.055 240)" />
                <Bar dataKey="bias" name="Bias (MW)" fill="oklch(0.58 0.15 35)" />
              </BarChart>
            </ResponsiveContainer>
          </section>

          <div className="section-head">
            <h2>Error by forecast horizon</h2>
            <span className="muted">all forecasts, any basis</span>
          </div>
          <section className="section-body">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byHorizon} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.9 0.013 245)" vertical={false} />
                <XAxis dataKey="bucket" tick={{ fontSize: 11 }} stroke="oklch(0.5 0.026 252)" />
                <YAxis width={64} tick={{ fontSize: 12 }} stroke="oklch(0.5 0.026 252)" tickFormatter={(v: number) => v.toLocaleString('en-GB')} />
                <Tooltip formatter={(v: unknown, n: unknown) => [num(typeof v === "number" ? v : null) + " MW", String(n)]} separator="· " />
                <Legend />
                <Bar dataKey="mae" name="MAE (MW)" fill="oklch(0.78 0.055 240)" />
                <Bar dataKey="bias" name="Bias (MW)" fill="oklch(0.58 0.15 35)" />
              </BarChart>
            </ResponsiveContainer>
          </section>
        </>
      )}
    </>
  )
}
