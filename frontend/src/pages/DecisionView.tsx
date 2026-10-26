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


function Stat({
  label,
  value,
  note,
  unit,
}: {
  label: string
  value: string
  note?: string
  unit?: string
}) {
  return (
    <div className="stat">
      <div className="stat-value">
        {value}
        {unit && <small>{unit}</small>}
      </div>
      <div className="stat-label">{label}</div>
      {note && <div className="stat-note">{note}</div>}
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
  const summary = decision.data?.summary

  const setParam = (key: 'date' | 'cutoff', value: string) => {
    setParams((prev) => {
      if (value) prev.set(key, value)
      else prev.delete(key)
      return prev
    })
  }

  return (
    <>
      <div className="page-head">
        <h1>Decision view</h1>
        <span className="provenance">
          Cutoff is 09:00 {cfg?.timezone ?? 'Europe/London'} on the day before delivery; every number
          below was knowable by then.
        </span>
      </div>

      <section className="toolbar">
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

      {decision.isPending && enabled && <p className="loading">Loading forecast…</p>}
      {decision.isError && <p className="error">Failed to load: {decision.error.message}</p>}

      {decision.data && summary && (
        <>
          <DataQualityBanner
            nMissingForecast={summary.n_missing_forecast}
            nMissingActual={summary.n_missing_actual}
          />

          <section className="stats">
            <Stat label="MAE" value={num(summary.mae_mw ?? null)} unit="MW" note="mean |error|" />
            <Stat label="RMSE" value={num(summary.rmse_mw ?? null)} unit="MW" note="penalises big misses" />
            <Stat
              label="Bias"
              value={num(summary.bias_mw ?? null)}
              unit="MW"
              note="mean error, + = over-forecast"
            />
            <Stat
              label="Suggested buffer"
              value={num(summary.suggested_buffer_mw ?? null)}
              unit="MW"
              note={
                summary.buffer_basis === 'full_period_fallback'
                  ? 'P90 of positive errors, full-period fallback'
                  : `P90 of positive errors, ${summary.buffer_sample_size} prior slots`
              }
            />
          </section>

          <div className="section-head">
            <h2>Forecast vs actual</h2>
            <span className="muted">
              {decision.data.delivery_date} · snapshot {decision.data.cutoff_local} · latest publish
              used {summary.latest_publish_time_used ?? 'none'}
            </span>
          </div>
          <section className="section-body">
            <ForecastChart rows={rows} bufferMw={summary.suggested_buffer_mw} />
            {summary.suggested_buffer_mw != null && (
              <p className="caption">
                Conservative wind = forecast − {num(summary.suggested_buffer_mw)} MW (P90 of positive
                errors from the {summary.buffer_sample_size} slots on days before this one
                {summary.buffer_basis === 'full_period_fallback' ? ', full-period fallback' : ''}).
                Indicative only.
              </p>
            )}
          </section>

          <div className="section-head">
            <h2>Slots</h2>
            <span className="muted">
              {summary.n_slots} half-hours · amber rows carry flags (missing forecast or actual)
            </span>
          </div>
          <section className="section-body">
            <div className="scrollbox">
              <table>
                <thead>
                  <tr>
                    <th>Slot (local)</th>
                    <th className="n">Forecast MW</th>
                    <th>Publish (UTC)</th>
                    <th className="n">Actual MW</th>
                    <th className="n">Error MW</th>
                    <th>Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.start_time} className={r.flags.length ? 'row-flagged' : ''}>
                      <td>{slotFmt.format(new Date(r.start_time))}</td>
                      <td className="n">{num(r.forecast_mw)}</td>
                      <td>{utc(r.publish_time)}</td>
                      <td className="n">{num(r.actual_mw)}</td>
                      <td className="n">{num(r.error_mw)}</td>
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
