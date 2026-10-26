# PRD: Wind Forecast Monitor for Day-Ahead Buying

## 1. Summary
A pilot web portal for a UK utility's day-ahead trading desk. It answers two questions about national wind generation:
1. "What was the latest wind forecast I had in hand at decision time for each half-hour of tomorrow?"
2. "How wrong are these forecasts typically, so I can buffer my purchases?"

## 2. Users
- **Primary: Day-ahead power buyer / trader.** Time-pressured, numerate, not a developer. Wants a clear chart and a few trustworthy numbers.
- **Secondary: Analyst / team lead.** Wants to inspect error by time of day and by forecast horizon.

## 3. Goals
- G1: Show the decision-time wind forecast for any delivery day in scope, next to actuals (once known).
- G2: Quantify forecast error (overall, by hour of day, by horizon) with well-defined metrics.
- G3: Turn error statistics into a decision aid: an error band around the forecast and a suggested "wind risk buffer" in MW.
- G4: Be fast, clear, deployed, reproducible (Docker), and explainable in a 10 minute video.

## 4. Non-goals
- No demand forecasting, no prices, no other fuel types, no other data sources.
- No auth, multi-tenancy, or database.
- No bidding/optimisation engine. We inform the decision, not make it.

## 5. Scope and key definitions
- Data window: purchase decisions made in **January 2026**. Each decision is made on day D-1 for delivery day D. See `DOMAIN_AND_ASSUMPTIONS.md` for the cutoff (default 09:00 Europe/London on D-1, configurable).
- Decision-time forecast for a target `startTime` = the forecast row with the greatest `publishTime` such that `publishTime <= cutoff(D-1)`.
- Error = forecast − actual (MW). Positive = over-forecast (dangerous: buyer under-buys).

## 6. Functional requirements

### FR1 Decision-time forecast view
- Date picker for delivery day (limited to the supported range) and a cutoff time control (default from config).
- Chart: 48 half-hour points. Series: decision-time forecast, actual (if available), optional error band.
- Show which `publishTime` each point's forecast came from (tooltip) and a summary: "Forecast snapshot as of <cutoff>; latest publish used: <timestamp>".
- Show data-quality flags: half-hours with no forecast available at cutoff, or no actual.
- Table below chart with startTime, forecast, publishTime, actual, error.

### FR2 Accuracy dashboard
- Date range selector (default: all of January).
- KPI cards: MAE, RMSE, Bias (mean error), MAPE-safe/normalised MAE (% of mean actual), P90 absolute error, coverage count (n points).
- Charts:
  - Forecast vs actual time series over the range.
  - Error distribution (histogram).
  - Error by hour of day (MAE and bias).
  - Error by forecast horizon (hours between `publishTime` and `startTime`), using all forecasts, to show how accuracy degrades with lead time.
- Toggle between "decision-time forecast" basis and "all horizons" basis where relevant.

### FR2b Leakage comparison
- On the accuracy page, show decision-time metrics next to naive metrics (latest forecast ever published, ignoring the cutoff). Include a plain-language caption: "Naive numbers look better because they use forecasts the buyer did not yet have."
- Chart or card showing the MAE gap overall and by delivery day.

### FR2c Key findings
- A findings panel (or `docs/FINDINGS.md` linked from the Methodology page) with 2-3 data-backed statements, e.g. how error grows with lead time, which hours are worst, over- vs under-forecast tendency.
- The app computes the supporting numbers; the human owner writes the conclusions. Agents must not fabricate findings.

### FR3 Decision aid
- For a chosen delivery day: "Suggested wind buffer" = P90 of positive errors only (definition in `DOMAIN_AND_ASSUMPTIONS.md`) from the historical data, expressed in MW, plus a "conservative wind" line = forecast − buffer. Clearly labelled as indicative and explain how it is computed.
- Must avoid look-ahead: when showing the buffer for day D, compute it only from delivery days before D (expanding window) with a documented minimum sample size, else fall back to the full-period value and flag it.

### FR4 Methodology page
- Static page explaining data sources, cutoff assumption, metric formulas, limitations. Reused in the video.

### FR5 Data handling
- Backend loads a committed January 2026 snapshot (fetched via `scripts/fetch_data.py` from Elexon) so the deployed app does not depend on Elexon uptime. A `/api/refresh` (optional, guarded) can re-pull.
- The snapshot must include forecast history from about 28 Dec 2025 (decisions for the first delivery days) and actuals through 1 Feb 2026. Document the exact fetch window and the verified API parameters.

## 7. Non-functional requirements
- Page load under 2 s on cached data; API responses under 500 ms for single-day queries.
- Responsive layout (laptop primary, tablet OK).
- Accessible colours/contrast; chart legends and units (MW) always visible.
- Reproducible: `docker compose up --build` works from a clean clone.
- Tests: unit tests for forecast selection and metrics; at least a few API tests.

## 8. Acceptance criteria
- AC1: For a known sample day, a test proves the selected forecast for each half-hour is the latest `publishTime` <= cutoff and no later forecast is used.
- AC2: Metrics match a hand-calculated fixture in tests.
- AC3: Changing the cutoff time visibly changes selected forecasts and the metrics.
- AC4: Missing data is reported (counts and flags), never silently ignored.
- AC5: App is deployed, public link works in incognito, and repo README is complete (incl. AI-tool disclosure).
- AC6: A test proves the naive (no-cutoff) comparison uses the latest publishTime overall and differs from the decision-time selection on a fixture.
- AC7: README and code contain no personal or employer identifiers (anonymous submission).
- AC8: A reviewer can understand the product in the 5 minute pitch and the code in the 5 minute tech review.

## 9. Success metrics for the pilot (talk track)
- Buyer can find the decision-time forecast in under 10 seconds.
- Quantified error (e.g. "typical error X MW, 90% of the time under Y MW") available for every delivery day.

## 10. Risks
- Cutoff ambiguity: the default is a placeholder until verified against the real gate closure time; configurable and documented.
- Elexon API shape/limits: verify against live docs, chunk requests by date, snapshot data.
- Timezone/DST bugs: UTC internally, tests around boundaries.
- Over-scoping: 16 hour cap; cut FR3 polish before cutting FR1/FR2/tests.
