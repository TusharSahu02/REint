# AGENTS.md

Instructions for AI coding agents working in this repo. Read this file first, then the docs listed below, before writing any code.

## Project in one paragraph
A web app for a UK energy utility's day-ahead power buying team. It shows (1) the latest national wind generation forecast that was available when the buyer had to decide (day-ahead, D-1), and (2) how accurate wind forecasts have been versus actual generation, with quantified error. Data comes ONLY from Elexon BMRS: FUELHH (actuals, fuelType=WIND) and WINDFOR (forecasts). Scope: decisions made in January 2026.

## Read these first (in order)
1. `docs/ORIGINAL_TASK.md` – the brief as given. Source of truth for scope.
2. `docs/PRD.md` – what to build and acceptance criteria.
3. `docs/DOMAIN_AND_ASSUMPTIONS.md` – domain rules, cutoff logic, metric definitions. Do not change these silently.
4. `docs/ARCHITECTURE.md` – structure, data flow, tech choices.
5. `docs/API_SPEC.md` – backend endpoints and response shapes (frontend and backend must match this).
6. `docs/TASKS.md` – milestones. Work through them in order; one milestone per commit group.
7. `docs/DEPLOYMENT.md` – Docker, Heroku, Vercel.
8. `docs/FINDINGS.md` – written by the human owner from the data. Do not invent its content; you may only compute the numbers it asks for.

## Tech stack (fixed)
- Backend: Python 3.12, FastAPI, pandas, httpx, pydantic v2, pytest, ruff
- Frontend: React 18 + Vite + TypeScript, Recharts, TanStack Query, plain CSS or Tailwind (pick one, keep it simple)
- Docker: one Dockerfile per service plus `docker-compose.yml` at the root
- No database. Data is a committed January 2026 snapshot (parquet or CSV) plus an optional live refresh.

## Repo layout (target)
```
/
├── AGENTS.md
├── README.md
├── docker-compose.yml
├── docs/
├── backend/
│   ├── app/ (main.py, config.py, api/, services/, models/)
│   ├── data/            # committed snapshot files
│   ├── scripts/fetch_data.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    ├── src/ (components/, pages/, api/, types/, hooks/)
    ├── Dockerfile
    └── package.json
```

## Commands (keep these working; update here if they change)
```
# backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest -q
ruff check . && ruff format .

# frontend
cd frontend && npm install
npm run dev
npm run build && npm run lint

# whole stack
docker compose up --build
```

## Rules
- **Anonymity:** the repo is submitted under an anonymous name. Never put real names, employer names, personal emails, personal URLs or usernames in code, docs, README, package metadata, Docker labels or commit messages. Use a neutral placeholder author in package.json / pyproject.
- **Inspect data first:** before writing selection or metrics code, run the fetch script, print raw samples from both endpoints and report what you see (publish frequency, forecast horizon range, duplicates, gaps, row counts) in `docs/DOMAIN_AND_ASSUMPTIONS.md` under "Verified API facts". Stop and show these findings before continuing to M2.
- **No leakage:** the app must also compute a deliberately naive comparison (latest forecast ever published for each slot, ignoring the cutoff) so the effect of the cutoff is visible. Naive numbers are for comparison only and must be labelled as not usable for decisions.
- Never hardcode Elexon endpoint parameters from memory. Open the live API docs/OpenAPI spec (https://bmrs.elexon.co.uk/api-documentation) and verify parameter names, formats and the response schema before writing the client. Record what you verified in `docs/DOMAIN_AND_ASSUMPTIONS.md`.
- All timestamps are stored and compared in UTC. Convert to `Europe/London` ONLY when computing the day-ahead cutoff and when displaying to the user. Handle BST/GMT correctly (January is GMT, but write code that is correct anyway).
- The decision-time forecast logic (latest `publishTime` <= cutoff for each `startTime`) is the core of this project. It must be a pure function in `services/forecast_selection.py` with unit tests. No lookahead leakage: never use a forecast published after the cutoff.
- Metrics live in `services/metrics.py` as pure functions with unit tests. Definitions are in `docs/DOMAIN_AND_ASSUMPTIONS.md`.
- Handle missing data explicitly (missing actuals, missing forecasts, duplicate rows). Never silently fill or drop; report counts in the API response.
- Backend responses must follow `docs/API_SPEC.md`. If you need to change a contract, update the spec in the same commit.
- Keep it small. Total budget for the whole assignment is 16 hours. Do not add auth, a database, user accounts, or extra datasets (the brief forbids data beyond Elexon wind).
- No secrets in the repo. Elexon BMRS data endpoints used here need no API key; if one is ever needed, use env vars and `.env.example`.
- Type everything: Python type hints, strict TypeScript (no `any`).
- Small commits with clear messages (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).

## Definition of done (per milestone)
- Code runs locally and in Docker.
- Tests for new logic pass (`pytest -q`), lint and type checks pass.
- `README.md` and docs updated if behaviour or commands changed.
- No TODOs left without a matching entry in `docs/TASKS.md`.

## README requirements (graded)
The final README must be written for an anonymous reviewer and contain: file/directory explanation, how to start the app (local and Docker), link to the deployed app, a short explanation of the cutoff assumption, and an explicit line stating that AI tools (Codex / ChatGPT / Claude) were used to assist development.

## When unsure
Prefer the simplest approach that satisfies the PRD. If the brief and these docs conflict, the brief (`docs/ORIGINAL_TASK.md`) wins. If something is ambiguous, state the assumption in `docs/DOMAIN_AND_ASSUMPTIONS.md` and continue rather than stopping.
