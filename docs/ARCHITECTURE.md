# Architecture

## Overview
```
Elexon BMRS API ──(scripts/fetch_data.py, offline)──> backend/data/*.parquet (committed snapshot)
                                                              │
Browser (React/Vite) ── HTTPS/JSON ──> FastAPI ── pandas ─────┘
```
Runtime reads the snapshot into memory at startup (small: ~1 month × 48 slots × many publish times). Optional `/api/refresh` re-fetches from Elexon.

## Backend (FastAPI)
- `app/main.py` – app factory, CORS (allow frontend origin from env), router mounting, lifespan loads data.
- `app/config.py` – settings via pydantic-settings: cutoff time, timezone, decision window, data path, CORS origins.
- `app/services/elexon_client.py` – thin httpx client with date chunking, retries, schema validation.
- `app/services/data_store.py` – loads snapshot into DataFrames (`actuals`, `forecasts`), exposes query helpers.
- `app/services/forecast_selection.py` – pure function: `select_decision_forecast(forecasts_df, delivery_date, cutoff) -> DataFrame`.
- `app/services/metrics.py` – pure functions for bias, MAE, RMSE, nMAE, percentiles, grouped metrics.
- `app/services/buffer.py` – expanding-window P90 over-forecast buffer.
- `app/api/routes.py` – endpoints per `API_SPEC.md`.
- `app/models/schemas.py` – pydantic response models.
- `tests/` – selection (cutoff edge cases), metrics (hand fixtures), API (TestClient).

Design principles: pure core logic, thin I/O layer, explicit data-quality counts in responses, config over constants.

## Frontend (React + Vite + TS)
- `src/api/client.ts` – typed fetch wrappers; types mirror `API_SPEC.md`.
- `src/pages/` – `DecisionView`, `Accuracy`, `Methodology`.
- `src/components/` – `ForecastChart`, `KpiCards`, `ErrorHistogram`, `HourOfDayChart`, `HorizonChart`, `DataQualityBanner`, `DatePicker`, `CutoffControl`, `Layout`.
- `src/hooks/` – TanStack Query hooks per endpoint.
- State: URL query params for date/cutoff (shareable links); server state via TanStack Query.
- UI: one clean layout with top nav, consistent MW units, loading/empty/error states.

## Data flow for FR1
1. UI requests `GET /api/decision-forecast?date=2026-01-15&cutoff=09:00`.
2. Backend computes cutoff timestamp (D-1 local → UTC), selects latest forecast per slot, joins actuals, computes error and buffer.
3. Returns 48 rows + summary + data-quality counts.

## Deployment topology
- Backend: Docker container listening on `$PORT` (`backend/Dockerfile`), deployed free-tier
  to Google Cloud Run or Render (`render.yaml`).
- Frontend: static build on Cloudflare Pages or Vercel (`frontend/vercel.json`); `VITE_API_BASE_URL` points to the backend.
- Local: `docker-compose.yml` runs both (backend :8000, frontend :3000 via nginx).

## Key engineering practices (for the tech review video)
- Pure functions + unit tests for the two things that matter (selection, metrics).
- Snapshot data for reproducibility and resilience.
- Typed contracts both sides; API spec doc.
- Config-driven assumptions.
- Linting/formatting, small commits, Docker parity with deploy.
