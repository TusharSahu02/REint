# Progress

## Current milestone plan (M0: scaffold)
1. git init, neutral identity, commit docs (done)
2. Backend tree: app/{api,services,models}+__init__.py, main.py, config.py, data/, scripts/, tests/ (done)
3. requirements.txt + ruff.toml (done)
4. Python venv (.venv), install requirements (done)
5. Frontend: vite react-ts, install recharts @tanstack/react-query react-router-dom (done)
6. Root .gitignore, .env.example (done)
7. Run M0 VERIFY commands, show real output (done)

## Log
- API facts verified pre-M1 (OpenAPI spec + live calls), recorded in docs/DOMAIN_AND_ASSUMPTIONS.md "Verified API facts". Key surprise: WINDFOR is HOURLY (not half-hourly) with irregular 2/3/4h publish cycles; owner decision pending on slot mapping before M2. Commit 879dcc1.
- M0: DONE. Scaffold committed. Backend health endpoint verified ({"status":"ok"}), ruff clean, frontend builds.
- Deviation: system python3.12 unavailable; local venv uses Python 3.10.16 (Dockerfile at M7 will pin 3.12-slim per DEPLOYMENT spec, so deploy parity is unaffected).
- Note: venv bootstrapped without ensurepip (python3.10-venv pkg missing on host); pip installed via get-pip.py into venv.

## Files created/changed (M0)
backend/app/{__init__,config,main}.py, backend/app/{api,services,models}/__init__.py
backend/{data,scripts,tests}/.gitkeep, backend/requirements.txt, backend/ruff.toml
frontend/ (vite react-ts scaffold + 3 deps), .gitignore, .env.example, PROGRESS.md

## Commands run / results
- pip install -r requirements.txt -> pass
- ruff check . -> pass
- python -c "from app.main import app" -> pass ("import ok")
- uvicorn :8000 + curl /api/health -> pass ({"status":"ok"})
- npm run build (frontend) -> pass (built in ~350ms)

## Open issues
- none
