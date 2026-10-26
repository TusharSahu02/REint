# Progress

## Log
- M0 DONE (30afc1d). M1 DONE (d4c524f). M1 follow-up DONE (77e369e/852d2fb). M2 DONE.
- M2: reference code ported VERBATIM (forecast_selection.py incl. expand_hourly_to_half_hourly, metrics.py, buffer.py) — zero logic changes. Tests: 15 collected, 15 passed (test_forecast_selection×8, test_metrics×4, test_buffer×3). venv python 3.10.16, ruff clean + format clean.
- M2 test notes: p90/p95 of |errors| for fixture [0,2,5] = 4.4 / 4.7 (linear interpolation); buffer minimum threshold counts strictly-positive errors only.
- Next: M3 API (routes per docs/API_SPEC.md, data_store lifespan load + expand call).

## Open issues
- none
