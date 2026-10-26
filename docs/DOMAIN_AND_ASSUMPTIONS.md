# Domain Knowledge and Assumptions

## Context
- GB day-ahead market: participants submit bids for delivery on day D before a gate closure on D-1 (the main auctions close around late morning UK time). Buyers therefore need forecasts that existed before that moment.
- Wind is a major, weather-driven supply source. Over-forecasting wind means the buyer under-procures and must cover the shortfall later at (usually worse) prices. Under-forecasting means over-buying.
- Elexon BMRS provides national half-hourly data (settlement periods are 30 minutes).

## Datasets
- **FUELHH** – half-hourly generation by fuel type. Filter `fuelType == "WIND"`. Use `startTime` and `generation` (MW).
- **WINDFOR** – wind generation forecasts. Fields: `startTime` (target), `publishTime` (when forecast was produced), `generation` (MW). The same `startTime` appears many times with different `publishTime` values.

- Elexon Insights API is public, no API key required. Base URL used by client libraries: `https://data.elexon.co.uk/bmrs/api/v1`.
- Stream endpoints: `/datasets/FUELHH/stream` and `/datasets/WINDFOR/stream` (docs pages linked in `ORIGINAL_TASK.md`).
- Exact query parameter names for the stream variants (publish-time vs settlement-date filters), date formats, maximum range per request and rate limits are **NOT yet verified**. The doc pages render with JavaScript, so open them in a browser or read the OpenAPI spec, then record the confirmed values below. Do not rely on memory.
- Fetch window: WINDFOR from about 28 Dec 2025 (decisions for early-January delivery days use late-December forecasts) through the last decision cutoff; FUELHH (WIND) from 1 Jan 2026 through 1 Feb 2026 (end of last delivery day). Widen if verification shows otherwise.

## Core assumption: the decision cutoff
- Default: forecast must satisfy `publishTime <= D-1 at 09:00 Europe/London` for delivery day D. **PLACEHOLDER: TO VERIFY** against the actual GB day-ahead auction gate closure time. The human owner will update this value and the rationale below; agents must not change it on their own.
- Rationale (to be replaced after verification): a round time before typical day-ahead gate closure. It is a **configurable parameter** (`DECISION_CUTOFF_LOCAL_TIME`, default `09:00`) and exposed in the UI.
- Delivery day D covers 00:00–24:00 Europe/London (48 half-hours in a normal day).
- "Decisions made in January 2026" is interpreted literally: decision dates 1–31 Jan 2026, so delivery days 2 Jan – 1 Feb 2026. This is a config constant (`DECISION_START`, `DECISION_END`) so it can be changed to "delivery days in January" in one place. State the choice in the README.

## Forecast selection algorithm
For each target `startTime` in delivery day D:
1. Candidate forecasts = rows with that `startTime` and `publishTime <= cutoff`.
2. Pick the one with max `publishTime`.
3. If none, mark the slot `missing_forecast`.
4. If duplicates share the same `publishTime`, keep the last-ingested and count the duplicates.

## Horizon
`horizon_hours = (startTime − publishTime)` in hours. Used for the horizon analysis.

## Metrics (all in MW unless stated)
Let e_t = forecast_t − actual_t over the n slots that have both.
- Bias (ME) = mean(e_t). Positive = over-forecast.
- MAE = mean(|e_t|).
- RMSE = sqrt(mean(e_t^2)).
- nMAE % = MAE / mean(actual) × 100 (use instead of MAPE because actual wind can be near zero).
- P50/P90/P95 of |e_t|.
- Over-forecast buffer (FR3), **decided definition**: the 90th percentile of e_t computed only over slots where e_t > 0 (forecast above actual). Meaning: when the forecast over-states wind, 9 times in 10 it does so by no more than this many MW. Slots with e_t <= 0 are excluded. Use linear interpolation percentile (numpy default). Require at least 30 positive-error slots, else flag as low-sample.
- Report n, number of missing forecasts, number of missing actuals.

## Naive comparison (leakage demonstration)
Naive forecast for a `startTime` = the forecast with the greatest `publishTime` in the whole dataset, ignoring any cutoff. It uses information the buyer did not have. Compute the same metrics for it and show them next to the decision-time metrics. Expect naive error to look smaller; the gap is the point.

## Data quality rules
- Parse timestamps as UTC (ISO 8601 with Z).
- De-duplicate actuals by `startTime`.
- Do not interpolate or fill. Exclude slots lacking either side from metrics, and count them.
- Verify there are 48 slots per day (46/50 on DST change days, not in scope for January).

## Verified API facts (fill in during M1)
- [ ] FUELHH endpoint, params, sample response
- [ ] WINDFOR endpoint, params, sample response
- [ ] Forecast horizon range observed (min/max hours)
- [ ] Publish frequency observed
- [ ] Any gaps in January 2026 data
