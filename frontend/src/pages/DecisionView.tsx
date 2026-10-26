import { useSearchParams } from 'react-router-dom'
import type { DecisionRow } from '../api/types'
import ForecastChart from '../components/ForecastChart'
import DataQualityBanner from '../components/DataQualityBanner'
import { apiBase } from '../api/client'
import { useAppConfig, useDecisionForecast } from '../hooks/useApi'

const slotFmt = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Europe/London',
  hour: '2-digit',
  minute: '2-digit',
})

const num = (v: number | null | undefined): string =>
  v == null ? '–' : v.toLocaleString('en-GB', { maximumFractionDigits: 1 })

const utc = (iso: string | null): string =>
  iso == null ? '–' : `${iso.slice(0, 16).replace('T', ' ')}Z`


function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="kpi">
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  )
}

export default function DecisionView() {
  const [params, setParams] = useSearchParams()
  const config = useAppConfig()
  const cfg = config.data

  const date = params.get('date') ?? cfg?.delivery_start ?? ''
  const cutoff = params.get('cutoff') ?? cfg?.cutoff_local_time ?? null
  const dateValid = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(date)
  const cutoffValid = cutoff == null || /^([01]\d|2[0-3]):[0-5]\d$/.test(cutoff)
  const inRange = Boolean(
    cfg && dateValid && date >= cfg.delivery_start && date <= cfg.delivery_end,
  )
  const enabled = inRange && cutoffValid

  const decision = useDecisionForecast(date, cutoff, enabled)
  const rows: DecisionRow[] = decision.data?.rows ?? []

  const setParam = (key: 'date' | 'cutoff', value: string) => {
    setParams((prev) => {
      if (value) prev.set(key, value)
      else prev.delete(key)
      return prev
    })
  }

  return (
    <>
      <section className="controls card">
        <label>
          Delivery day
          <input
            type="date"
            value={date}
            min={cfg?.delivery_start}
            max={cfg?.delivery_end}
            onChange={(e) => setParam('date', e.target.value)}
            disabled={!cfg}
          />
        </label>
        <label>
          Cutoff ({cfg?.timezone ?? 'Europe/London'})
          <input
            type="time"
            value={cutoff ?? ''}
            onChange={(e) => setParam('cutoff', e.target.value)}
            disabled={!cfg}
          />
        </label>
      </section>

      {config.isError && (
        <div className="banner" role="status">
          Backend unreachable at {apiBase}. Start it with: uvicorn app.main:app --port 8000
        </div>
      )}
      {dateValid && !inRange && cfg && (
        <div className="banner" role="status">
          Delivery day {date || '(empty)'} is outside the supported range {cfg.delivery_start}–{cfg.delivery_end}.
        </div>
      )}
      {dateValid && !cutoffValid && <div className="banner">Cutoff must be a local time like 09:00.</div>}

      {decision.isPending && enabled && <p>Loading…</p>}
      {decision.isError && <p className="error">Failed to load: {decision.error.message}</p>}

      {decision.data && (
        <>
          <DataQualityBanner
            nMissingForecast={decision.data.summary.n_missing_forecast}
            nMissingActual={decision.data.summary.n_missing_actual}
          />

          <section className="kpis">
            <Kpi label="MAE (MW)" value={num(decision.data.summary.mae_mw)} />
            <Kpi label="RMSE (MW)" value={num(decision.data.summary.rmse_mw)} />
            <Kpi
              label="Bias (mean error, MW)"
              value={num(decision.data.summary.bias_mw)}
            />
            <Kpi
              label="Suggested buffer (MW)"
              value={
                num(decision.data.summary.suggested_buffer_mw) +
                (decision.data.summary.buffer_basis === 'full_period_fallback'
                  ? ' (full-period fallback)'
                  : '')
              }
            />
          </section>

          <section className="card">
            <h2>
              Forecast vs actual — {decision.data.delivery_date}
            </h2>
            <p className="muted">
              Snapshot as of {decision.data.cutoff_local}; latest publish used:{' '}
              {decision.data.summary.latest_publish_time_used ?? 'none'}
            </p>
            <ForecastChart rows={rows} />
          </section>

          <section className="card">
            <h2>Slots ({decision.data.summary.n_slots})</h2>
            <div className="scrollbox">
              <table>
                <thead>
                  <tr>
                    <th>Slot (local)</th>
                    <th>Forecast MW</th>
                    <th>Publish (UTC)</th>
                    <th>Actual MW</th>
                    <th>Error MW</th>
                    <th>Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.start_time} className={r.flags.length ? 'row-flagged' : ''}>
                      <td>{slotFmt.format(new Date(r.start_time))}</td>
                      <td>{num(r.forecast_mw)}</td>
                      <td>{utc(r.publish_time)}</td>
                      <td>{num(r.actual_mw)}</td>
                      <td>{num(r.error_mw)}</td>
                      <td>{r.flags.join(', ') || '–'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  )
}
