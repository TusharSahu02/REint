# Progress

## Log
- M0 DONE (30afc1d). M1 DONE (d4c524f). M1 follow-up DONE (77e369e/852d2fb). M2 DONE.
- M2: reference code ported VERBATIM (forecast_selection.py incl. expand_hourly_to_half_hourly, metrics.py, buffer.py) — zero logic changes. Tests: 15 collected, 15 passed (test_forecast_selection×8, test_metrics×4, test_buffer×3). venv python 3.10.16, ruff clean + format clean.
- M2 test notes: p90/p95 of |errors| for fixture [0,2,5] = 4.4 / 4.7 (linear interpolation); buffer minimum threshold counts strictly-positive errors only.
- M3 DONE: backend API.
  - Files: app/config.py (+delivery_start/end properties), app/services/data_store.py (lifespan load, tz validation, expand once, raw counts), app/services/frames.py (decision/naive frames lru-cached, all_horizon_frame, to_json_safe), app/models/schemas.py (pydantic v2 response models), app/api/routes.py (/health /config /decision-forecast /accuracy), app/main.py (lifespan, CORS, logging, 500 handler), tests/test_api.py (10 new tests).
  - Commands: pytest → 25 passed (15 M2 + 10 M3); ruff check + format --check clean; pinned requirements (uv pip install), pytest re-run green; live uvicorn checks pass (config/decision-forecast/accuracy JSON, 400 for 2026-03-01), /api/accuracy timing first 0.30s / cached 0.26s.
  - Real-data check (uncommitted scratch, /tmp/check_real_data.py): 31×48 rows, 0 missing_forecast, publish ≤ cutoff everywhere; decision n=1488 mae=2041.96 nmae=18.10% bias=+1747.9; naive n=1488 mae=1666.77 nmae=14.77% bias=+1491.6 → naive < decision as expected.
  - Behaviour notes added to docs/API_SPEC.md (health counts are raw pre-expansion rows; by_hour always 24 entries; buffer fallback semantics; 404 only for truly empty ranges).
- Next: M4 frontend.

## M3 plan
- config.py: computed delivery_start/end properties (decision + 1 day), env-overridable unchanged.
- data_store.py: load actuals+forecasts parquet at startup (lifespan), validate tz-aware UTC, fail loudly, expand once; keep actuals + expanded + raw row counts, info() helper.
- frames.py (new): decision_frame/naive_frame (lru_cache per date+cutoff, joined to actuals, error_mw, delivery_date), all_horizon_frame (non-negative horizon, both present), to_json_safe (NaN/NaT/inf→None, numpy→python, ts→ISO Z).
- schemas.py: pydantic v2 models per API_SPEC field names; Optional for nullable metrics.
- routes.py: /health /config /decision-forecast /accuracy under /api; expanding-window buffer w/ full-period fallback; validation 400s; 404 only when range truly empty; all output via to_json_safe.
- main.py: lifespan load, router mount, CORS from settings, stdlib logging, 500 {"detail":"internal error"} handler.
- tests/test_api.py: 14+ tests vs real parquet, TestClient context manager (lifespan runs).
- Verify: pytest, ruff, live curl checks, accuracy timing; real-data script in /tmp (not committed); pin requirements; commit "feat: backend API with tests".

## M3.5 plan
- Read-only bias diagnostic; no changes to services/routes/tests.
- backend/scripts/diagnose_bias.py (committed): load parquets, expand, decision+naive frames for 31 days @09:00 via existing services.
- Sections: 1 levels+ratio+corr; 2 error vs horizon incl. negative buckets; 3 shift test k=-6..6 (30-min) + hourly :00 shifts ±3h, decision & naive; 4 by-actual-level bins; 5 by London hour; 6 by day (count positive); 7 sample day 2026-01-15; 8 one FUELHH network call (no fuelType filter, 2026-01-15) scope check; 9 raw WINDFOR semantics for 2026-01-15T12:00Z.
- Rank H1-H4 hypotheses in final interpretation from printed evidence.
- Verify: run script, ruff check/format clean, pytest still 25, git status shows only script+PROGRESS; commit "chore: add bias diagnostic script".

## Open issues
- none
