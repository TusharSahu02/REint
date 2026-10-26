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
- M0: DONE (30afc1d). M1: DONE (d4c524f).
- Pre-M1 facts (879dcc1): WINDFOR HOURLY, cadence 2/3/4h (mostly), day-scale chunks; FUELHH half-hourly, publish = slot + 30min.
- M1 outputs: actuals.parquet 1488 rows (0 missing slots Jan); forecasts.parquet 20440 rows, 280 cycles, horizon −25.5/21.5/66.5h, 0 dups, 0 NaN.
- Next: M2 core logic — BLOCKED on owner decision: WINDFOR hourly forecast → half-hour slot mapping (proposal in DOMAIN doc: hourly MW covers both slots of the hour).

## Open issues
- WINDFOR hourly-vs-half-hourly slot mapping (owner decision before M2).
