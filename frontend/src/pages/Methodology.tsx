import { Link } from 'react-router-dom'

type QA = {
  q: string
  note?: string
  children: React.ReactNode
}

function QAItem({ index, q, note, children }: QA & { index: number }) {
  return (
    <article className="qa">
      <span className="qa-num">{String(index).padStart(2, '0')}</span>
      <h2 className="qa-q">{q}</h2>
      {note && <p className="qa-note">{note}</p>}
      <div className="qa-a">{children}</div>
    </article>
  )
}

export default function Methodology() {
  const items: QA[] = [
    {
      q: 'What is this app?',
      children: (
        <p>
          A monitoring portal for day-ahead national wind purchasing. It shows (1) the wind forecast
          that was in hand when a buyer had to decide for each half-hour of a delivery day, and (2)
          how accurate these forecasts have been, to size a purchase buffer.
        </p>
      ),
    },
    {
      q: 'Where does the data come from?',
      note: 'Elexon BMRS only',
      children: (
        <p>
          Actual wind generation comes from the FUELHH dataset (fuelType=WIND); forecasts from the
          WINDFOR dataset. Both are fetched offline by <code>backend/scripts/fetch_data.py</code> and
          committed as a snapshot covering delivery days 2026-01-02 to 2026-02-01 (with forecast
          history from late December 2025). The deployed app does not depend on Elexon uptime.
        </p>
      ),
    },
    {
      q: 'What is the decision-time cutoff?',
      note: 'no look-ahead leakage',
      children: (
        <p>
          A buyer for delivery day D decides on day D-1. We assume the decision cutoff is 09:00
          Europe/London on D-1 (configurable, and a placeholder until verified against the real gate
          closure time). For every half-hour slot of day D we take the WINDFOR forecast with the{' '}
          <em>latest publishTime</em> that was published at or before the cutoff. Forecasts published
          after the cutoff are never used for decision metrics: using them would leak information from
          the future.
        </p>
      ),
    },
    {
      q: 'Why is there a "naive" comparison?',
      children: (
        <p>
          The naive comparison deliberately ignores the cutoff and uses the latest forecast ever
          published for each slot. It looks better, but the buyer did not have those forecasts at
          decision time, so naive numbers are shown only to demonstrate the effect of the cutoff,
          never as a decision benchmark.
        </p>
      ),
    },
    {
      q: 'What do the metrics mean?',
      children: (
        <>
          <p>
            Error = forecast − actual (MW). Positive error = over-forecast (the buyer under-buys).
          </p>
          <dl className="defs">
            <div>
              <dt>MAE</dt>
              <dd>mean absolute error</dd>
            </div>
            <div>
              <dt>RMSE</dt>
              <dd>root mean squared error, penalises big misses</dd>
            </div>
            <div>
              <dt>Bias</dt>
              <dd>mean error; negative values mean systematic under-forecast</dd>
            </div>
            <div>
              <dt>nMAE</dt>
              <dd>MAE as a percentage of mean actual generation</dd>
            </div>
            <div>
              <dt>P90 abs error</dt>
              <dd>90% of half-hours had an absolute error at or below this value</dd>
            </div>
          </dl>
        </>
      ),
    },
    {
      q: 'What is the suggested buffer?',
      note: 'indicative, not an optimiser',
      children: (
        <p>
          The suggested buffer is the 90th percentile (P90) of positive errors only (over-forecasts),
          computed from delivery days <em>before</em> the selected day (expanding window, minimum 30
          samples, falling back to the full period and flagged if fewer). Conservative wind =
          forecast − buffer. Both are indicative, not an optimiser.
        </p>
      ),
    },
    {
      q: 'What are the data quality limits?',
      children: (
        <ul>
          <li>
            Missing data is never filled silently: half-hours without an in-hand forecast or without
            an actual are flagged and excluded from metrics, with counts shown.
          </li>
          <li>
            WINDFOR is published hourly; half-hourly slots reuse the covering hourly forecast
            (step-hold), so two half-hours share one forecast value.
          </li>
          <li>January 2026 only: results describe one winter month, not a full year of conditions.</li>
          <li>
            National fleet only: no per-region or per-farm view, and no demand or price data. The
            suggested purchase volume itself is out of scope.
          </li>
        </ul>
      ),
    },
    {
      q: "Where are the owner's findings?",
      children: (
        <p>
          The human owner's interpretation of the numbers lives in <code>docs/FINDINGS.md</code> in the
          repository. This app reports the supporting statistics (by horizon, by hour of day, by day,
          and the leakage comparison).
        </p>
      ),
    },
  ]

  return (
    <>
      <div className="page-head">
        <h1>Methodology</h1>
        <span className="provenance">what the numbers mean, exactly, and where they come from</span>
      </div>

      <div className="article">
        <p className="lede">
          Everything this app claims, in eight questions. Read this once and the decision view and the
          accuracy dashboard stop being black boxes.
        </p>

        {items.map((item, i) => (
          <QAItem key={item.q} index={i + 1} {...item} />
        ))}

        <footer className="article-foot">
          <Link to="/accuracy">Back to the accuracy dashboard.</Link>
        </footer>
      </div>
    </>
  )
}
