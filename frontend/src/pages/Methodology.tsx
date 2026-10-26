import { Link } from 'react-router-dom'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {children}
    </section>
  )
}

export default function Methodology() {
  return (
    <>
      <Section title="What this app is">
        <p>
          A monitoring portal for day-ahead national wind purchasing. It shows (1) the wind
          forecast that was in hand when a buyer had to decide for each half-hour of a delivery
          day, and (2) how accurate these forecasts have been, to size a purchase buffer.
        </p>
      </Section>

      <Section title="Data sources">
        <p>
          Elexon BMRS only. Actual wind generation comes from the FUELHH dataset (fuelType=WIND);
          forecasts from the WINDFOR dataset. Both are fetched offline by{' '}
          <code>backend/scripts/fetch_data.py</code> and committed as a snapshot covering delivery
          days 2026-01-02 to 2026-02-01 (with forecast history from late December 2025). The
          deployed app does not depend on Elexon uptime.
        </p>
      </Section>

      <Section title="The decision-time cutoff">
        <p>
          A buyer for delivery day D decides on day D-1. We assume the decision cutoff is 09:00
          Europe/London on D-1 (configurable, and a placeholder until verified against the real
          gate closure time). For every half-hour slot of day D we take the WINDFOR forecast with
          the <em>latest publishTime</em> that was published at or before the cutoff. Forecasts
          published after the cutoff are never used for decision metrics — using them would leak
          information from the future.
        </p>
        <p>
          The "naive" comparison deliberately ignores the cutoff and uses the latest forecast ever
          published for each slot. It looks better, but the buyer did not have those forecasts at
          decision time — so naive numbers are shown only to demonstrate the effect of the cutoff,
          never as a decision benchmark.
        </p>
      </Section>

      <Section title="Metric definitions">
        <p>Error = forecast − actual (MW). Positive error = over-forecast (the buyer under-buys).</p>
        <ul>
          <li>MAE — mean absolute error; RMSE — root mean squared error.</li>
          <li>Bias — mean error; negative values mean systematic under-forecast.</li>
          <li>nMAE — MAE as a percentage of mean actual generation.</li>
          <li>P90 abs error — 90% of half-hours had an absolute error at or below this value.</li>
        </ul>
        <p>
          <strong>Suggested buffer</strong> = the 90th percentile (P90) of positive errors only
          (over-forecasts), computed from delivery days <em>before</em> the selected day
          (expanding window, minimum 30 samples, falling back to the full period and flagged if
          fewer). <strong>Conservative wind</strong> = forecast − buffer. Both are indicative, not
          an optimiser.
        </p>
      </Section>

      <Section title="Data quality and limitations">
        <ul>
          <li>
            Missing data is never filled silently: half-hours without an in-hand forecast or
            without an actual are flagged and excluded from metrics, with counts shown.
          </li>
          <li>
            WINDFOR is published hourly; half-hourly slots reuse the covering hourly forecast
            (step-hold), so two half-hours share one forecast value.
          </li>
          <li>
            January 2026 only: results describe one winter month, not a full year of conditions.
          </li>
          <li>
            National fleet only: no per-region or per-farm view, and no demand or price data —
            the suggested purchase volume itself is out of scope.
          </li>
        </ul>
      </Section>

      <Section title="Owner's findings">
        <p>
          The human owner's interpretation of the numbers lives in{' '}
          <code>docs/FINDINGS.md</code> in the repository. This app reports the supporting
          statistics (by horizon, by hour of day, by day, and the leakage comparison).
        </p>
        <p>
          <Link to="/accuracy">Back to the accuracy dashboard.</Link>
        </p>
      </Section>
    </>
  )
}
