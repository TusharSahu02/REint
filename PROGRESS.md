# Progress

## Current milestone plan (M1: fetch + profile, ≤10 lines)
1. fetch_data.py: httpx, WINDFOR day-chunks 2025-12-28→2026-02-01T00:00Z; FUELHH WIND 01-01→02-01
2. Retry x3 (2/4/8s), clear error, verified params only (see DOMAIN doc)
3. Normalise → actuals.parquet (start_time UTC, actual_mw), forecasts.parquet (+publish_time UTC, forecast_mw)
4. Drop exact dups, never fill, print counts
5. profile_data.py: counts, min/max times, distinct publishTimes + gap, horizon stats, dup pairs, missing slots, 5 samples
6. Run for real, show output
7. Update DOMAIN doc "Verified API facts" with real profile numbers; commit

## Log
- M0: DONE (commit 30afc1d). Scaffold, venv py3.10.16, all VERIFY pass. Deviation: py3.12 unavailable locally; Docker (M7) pins 3.12-slim.
- Pre-M1: API facts verified from OpenAPI spec + live calls, recorded in DOMAIN doc (commit 879dcc1). WINDFOR = HOURLY, irregular 2/3/4h publish cycles, day-scale chunks needed. Owner slot-mapping decision pending before M2.
- M1: in progress.

## Files changed (latest milestone)
- backend/scripts/fetch_data.py (new)
- backend/scripts/profile_data.py (new)
- backend/data/{actuals,forecasts}.parquet (generated)
- docs/DOMAIN_AND_ASSUMPTIONS.md (profile numbers appended)
- PROGRESS.md

## Commands run / results
- python backend/scripts/fetch_data.py -> pending
- python backend/scripts/profile_data.py -> pending
- ls -la backend/data -> pending

## Open issues
- WINDFOR hourly-vs-half-hourly slot mapping (owner decision before M2).
