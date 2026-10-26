# Wind Forecast Monitor

A pilot web portal for a UK energy utility's day-ahead power buying team. It answers two questions:

1. **Decision view** — for any delivery day in January 2026, what was the latest national wind forecast the buyer had *in hand* for each half-hour, next to the actual wind generation once known?
2. **Accuracy dashboard** — how wrong have these been, quantified (MAE, RMSE, bias, nMAE, P90), by hour of day and by forecast lead time, so purchase volume can be buffered.

Data comes exclusively from the Elexon BMRS APIs: actuals from `FUELHH` (fuelType=WIND) and forecasts from `WINDFOR`. A committed January 2026 snapshot makes the app reproducible and independent of Elexon uptime; an optional refresh endpoint can re-pull.

**AI tool disclosure:** AI coding tools (Codex / ChatGPT / Claude) were used to assist development of this repository.

## How the decision-time cutoff works

A buyer for delivery day **D** decides on day **D-1**. This app assumes that decision closes at **09:00 Europe/London on D-1** (configurable; a placeholder until verified against the real gate closure time). For every half-hour slot of D the app picks the forecast with the **latest `publishTime` at or before that cutoff** — never anything published later, because the buyer could not have seen it. All timestamps are handled in UTC internally; Europe/London is applied only for the cutoff and display, so GMT/BST are handled correctly.

The accuracy dashboard shows a deliberately **naive** comparison — the latest forecast ever published per slot, ignoring the cutoff — to make the cost of the cutoff visible. Naive numbers look better but are explicitly labelled as not usable for decisions.

## Repository structure

```
/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app factory, CORS, lifespan data load, error handler
│   │   ├── config.py          # pydantic-settings: cutoff, window, data dir, CORS
│   │   ├── api/routes.py      # /api endpoints (per docs/API_SPEC.md)
│   │   ├── models/schemas.py  # pydantic response models
│   │   └── services/
│   │       ├── data_store.py            # loads committed snapshot, validates, expands hourly→half-hourly
│   │       ├── forecast_selection.py    # pure decision-time / naive selection (no lookahead)
│   │       ├── metrics.py               # pure metric functions
│   │       └── buffer.py                # P90 over-forecast buffer
│   ├── data/                  # committed parquet snapshot (actuals.parquet, forecasts.parquet)
│   ├── scripts/               # fetch_data.py (offline snapshot fetch), diagnose_bias.py (read-only diagnostics)
│   ├── tests/                 # pytest: selection edge cases, metric fixtures, API tests
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/               # typed fetch client + response types (mirror of API spec)
│       ├── components/        # ForecastChart, DataQualityBanner, Layout
│       ├── hooks/useApi.ts    # TanStack Query hooks
│       └── pages/             # DecisionView, Accuracy, Methodology
├── docker-compose.yml         # full stack locally (backend :8000, frontend :3000)
├── render.yaml                # backend free web service (Render blueprint)
└── docs/                      # original task brief, PRD, API spec, domain assumptions, deployment
```

## Run locally (no Docker)

Backend (Python 3.12):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (Node 18+):

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173, proxies to the backend via CORS
npm run build && npm run lint
```

Useful backend commands: `pytest -q`, `ruff check . && ruff format .`. Frontend: `npm run lint`.

## Run with Docker

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (API docs at `/docs`)
- Frontend: http://localhost:3000 (nginx serves the built app and proxies `/api` to the backend)

## Deployed app

Not yet deployed from this repository snapshot. Free-tier deployment paths (no card
required: Vercel + Render; no sleep and no card charges: Cloudflare Pages + Google
Cloud Run; single-service: FastAPI serving the built SPA) are documented step by step in
`docs/DEPLOYMENT.md`, together with the CORS and `VITE_API_BASE_URL` settings and the
incognito verification checklist. `render.yaml` and `frontend/vercel.json` are ready in
the repo.

## API

All endpoints are documented in `docs/API_SPEC.md`:

- `GET /api/health`
- `GET /api/config`
- `GET /api/decision-forecast?date=YYYY-MM-DD&cutoff=HH:mm`
- `GET /api/accuracy?start=YYYY-MM-DD&end=YYYY-MM-DD&basis=decision|all_horizons&cutoff=HH:mm`
- `POST /api/refresh` (optional, token-guarded)

Missing data is never silently filled: half-hours without an in-hand forecast or an actual are flagged and counted in every response.

## Data snapshot

`backend/scripts/fetch_data.py` fetched and verified both datasets against the live Elexon API (parameter names and schemas documented in `docs/DOMAIN_AND_ASSUMPTIONS.md`). Scope: delivery days 2026-01-02 → 2026-02-01, with forecast history from late December 2025 so early delivery days have an in-hand forecast. Read-only statistics produced during the build live in `docs/`; the owner's conclusions live in `docs/FINDINGS.md`.
