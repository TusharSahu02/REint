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

## Verified API facts

Verified against the live OpenAPI spec (`https://data.elexon.co.uk/swagger/v1/swagger.json`, discovered from the JS bundle of `https://bmrs.elexon.co.uk/api-documentation`) and real responses fetched 2026-10-26.

### Base URL
`https://data.elexon.co.uk/bmrs/api/v1` — public, no API key.

### FUELHH (actual generation by fuel type)
- Path: `GET /datasets/FUELHH/stream`
- Verified params: `settlementDateFrom` / `settlementDateTo` (format `YYYY-MM-DD`), `settlementPeriod` (array of int, optional), `fuelType` (array of string, e.g. `WIND`); also `publishDateTimeFrom/To` (ISO 8601 with `Z`).
- Fields per row: `dataset, publishTime, startTime, settlementDate, settlementPeriod, fuelType, generation`.
- January-2026 actuals observed: 1536 rows (WIND, 2026-01-01 → 2026-02-01 inclusive, 48 half-hour slots/day), every `startTime` unique, no duplicates.
- `publishTime = startTime + 30 min` for every observed row (actuals published right after each period).
- Row order is newest-first.
- Sample row:
```json
{"dataset":"FUELHH","publishTime":"2026-02-01T23:30:00Z","startTime":"2026-02-01T23:00:00Z","settlementDate":"2026-02-01","settlementPeriod":47,"fuelType":"WIND","generation":5130}
```

### WINDFOR (national wind forecast)
- Path: `GET /datasets/WINDFOR/stream`
- Verified params: `publishDateTimeFrom` / `publishDateTimeTo` (ISO 8601 with `Z`). No settlement-date filters.
- Fields per row: `dataset, publishTime, startTime, generation`.
- **Row granularity is HOURLY**: across all 18,104 rows for January 2026, not a single `startTime` had minutes=30. StartTimes run hourly (e.g. `21:00, 22:00, 23:00`).
- Publish cycle: exactly 73 rows per `publishTime` (a rolling ~72h horizon window), and every row of a cycle shares one `publishTime`. January 2026 shows 248 distinct cycles; consecutive-cycle gaps are irregular and only ever 120 / 180 / 240 minutes (plus two one-off 175/185-min gaps), i.e. cycles are NOT on a fixed half-hourly schedule.
- A ~1-hour publish window returned `[]` (unreliable below ~day-scale); use **day-size chunks** (`from` = day 00:00Z) for fetching. One month ≈ 18k rows per chunked month is fine.
- Sample row:
```json
{"dataset":"WINDFOR","publishTime":"2026-01-01T22:30:00Z","startTime":"2025-12-31T21:00:00Z","generation":19498}
```

### Inconsistency discovered (needs owner decision before M2)
- DOMAIN doc expected half-hourly forecasts: **reality is hourly** WINDFOR. Proposal: distribute the hourly forecast equally to both half-hour slots (`HH:00` covers the whole hour, wind MW is average power over the hour). → decision slots still 48/day, slot-level forecast = hourly MW.
- WINDFOR horizon: each cycle spans startTime up to ~3 days ahead of publish (M1 profiling script will compute exact min/median/max horizon in hours).

### Fetching rules (verified)
- All datetimes ISO 8601 UTC with `Z` suffix (400 "DateTime should be in ISO format" otherwise).
- FUELHH: filter `fuelType=WIND`; dates by settlement window.
- WINDFOR: chunk by published-day (00:00Z → next 00:00Z), range 2025-12-28 → 2026-02-01 per fetch win.
- Drop exact duplicate rows after fetch; never fill missing values.
- No rate limit observed at the explore pace used (single calls, seconds apart). Keep fetch polite: chunked days, small sleep between requests.
