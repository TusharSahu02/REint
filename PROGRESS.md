# Progress

## Current milestone plan
- Next: M2 core logic (reference code from owner PROMPT.md §D + addendum).

## M2 addendum from owner (deliver with M2)
- Add `expand_hourly_to_half_hourly(forecasts)` to `forecast_selection.py` (code pasted by owner in the session; step-hold: hourly row → both `:00`/`:30` slots) and call it once when data loads.
- Extra M2 tests: (1) expansion doubles rows, `:30` rows share publish_time + forecast_mw of their `:00` row; (2) selection returns 48 slots, no `missing_forecast`, on an hourly fixture; (3) expansion raises on `:30` rows.

## Log
- M0 DONE (30afc1d). M1 DONE (d4c524f). Pre-M1 API facts (879dcc1).
- Follow-up fix DONE: actuals window extended to `startTime < 2026-02-02T00:00Z` → **1536 rows, 0 missing**. WINDFOR window unchanged (last cutoff 31 Jan 09:00 LON).
- Hourly step-hold VERIFIED on raw data: 0/20,440 rows off the hour; every cycle 73 hourly rows (earliest 2025-12-28 02:30Z covers 2025-12-27 21:00 → 2025-12-30 21:00; middle 2026-01-14 11:30Z same span; latest 2026-01-31 22:30Z covers 2026-01-30 21:00 → 2026-02-02 21:00).
- Coverage check added + passed standalone: **31/31 delivery days at 24/24** hourly coverage from the latest cycle ≤ cutoff (cycle always D-1 07:30Z).
- Negative-horizon rule recorded: keep h<0 rows; horizon analysis excludes them; cutoff filter protects selection.
- Note: `datetime.UTC` alias (ruff UP017 autofix) is py3.11+ — dev venv is 3.10; UP017 now ignored in ruff.toml (Docker/3.12 unaffected).
- Next: M2 core logic — unblocked, see addendum above.

## Open issues
- none
