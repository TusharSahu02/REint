# OpenCode + GLM Flash: Prompt Playbook

Why this is split into many prompts: a free "flash" model with a lighter harness loses track of long instructions, invents API details, and drifts after many tool calls. So: one milestone per fresh session, explicit file lists, explicit verify commands, hard stop rules, and a PROGRESS.md file that carries state between sessions.

## 0. Your workflow (do this yourself, not the model)

1. Create the repo with a neutral git identity, then commit the docs:
   - `git init && git config user.name "dev" && git config user.email "dev@example.com"` (inside this repo only)
   - copy `AGENTS.md` to the repo root and the rest to `docs/`
   - `git add . && git commit -m "docs: add specs"`
2. Verify the Elexon API yourself with curl/browser BEFORE M1 and keep the working URLs and one sample response each. Weak models hallucinate parameter names. You will paste your verified facts into the M1 prompt.
3. Run ONE milestone per session. Start a fresh session (new chat) for each. Paste the Master Prompt, then the milestone prompt.
4. After every milestone: run the verify commands yourself, read the diff (`git diff --stat`, skim key files), then `git commit`. If the model wrecks something, `git reset --hard` and re-run with a tighter prompt.
5. For the two logic files that matter (forecast selection and metrics) do NOT let the model design them. Section D has reference code. Paste it and ask the model only to place it and write tests.
6. If a milestone fails 3 times, stop. Paste the error to me (Claude) or fix by hand. Do not let it loop.
7. Keep the model on one language at a time per prompt (backend prompts, then frontend prompts). Mixed prompts cause skipped work.

---

## A. Master Prompt (paste at the start of EVERY session)

```text
You are the implementation agent for a take-home project: a wind-forecast monitoring web app (FastAPI backend, React + Vite + TypeScript frontend, Docker). You work in this repository only.

STARTUP (do these first, in order, and tell me when done):
1. Read AGENTS.md fully.
2. Read PROGRESS.md if it exists (it is your memory between sessions). If it does not exist, create it with the heading "# Progress" and nothing else.
3. Read only the docs files that my milestone prompt names.

HARD RULES:
- Work ONLY on the milestone I name below. Do not start the next milestone. Do not refactor or "improve" unrelated files.
- Do not change anything under docs/ unless the milestone prompt explicitly says to.
- Never invent Elexon API parameters, endpoints, or response fields. Use only what I provide in the prompt or what you observe from a real response you fetched and printed.
- Never use a library or version I did not list unless you tell me first and explain why.
- All timestamps stay UTC, tz-aware. Convert to Europe/London only for the cutoff calculation and display.
- Never write real names, emails, employer names or personal URLs anywhere (anonymous submission).
- Type hints in Python, strict TypeScript with no `any`.
- Do not use placeholder code like "TODO", "pass", "...", or fake data to make something look finished. If you cannot complete something, say so.

WORKING METHOD:
1. Before editing, write a plan of at most 10 lines to PROGRESS.md under "## Current milestone plan".
2. Implement in small steps. After each step, run the verification commands for that step and show me their real output.
3. If a command fails: read the error, fix the cause, re-run. After 3 failed attempts at the same problem, STOP and report: the exact error, what you tried, and your best hypothesis. Do not keep looping.
4. When done, run every command in the milestone's "VERIFY" section and show the real output.
5. Update PROGRESS.md: what was done, files created or changed, commands run with pass/fail, open issues.
6. End with this exact summary format:
   DONE: <list>
   NOT DONE: <list or "none">
   FILES CHANGED: <list>
   VERIFY RESULTS: <command -> pass/fail>
   QUESTIONS FOR ME: <list or "none">
Then stop and wait.
```

---

## B. Milestone prompts (paste ONE after the Master Prompt)

### M0: Scaffold

```text
MILESTONE M0: project scaffold. Read: AGENTS.md, docs/ARCHITECTURE.md, docs/DEPLOYMENT.md.

Create exactly this structure (empty folders need a .gitkeep):
- backend/app/{api,services,models}/ with __init__.py files, backend/app/main.py, backend/app/config.py
- backend/data/, backend/scripts/, backend/tests/
- backend/requirements.txt with: fastapi, uvicorn[standard], pandas, pyarrow, numpy, httpx, pydantic, pydantic-settings, tzdata, pytest, ruff
- backend/ruff.toml (line-length 100)
- frontend/ created with: npm create vite@latest frontend -- --template react-ts, then install: recharts @tanstack/react-query react-router-dom
- Root .gitignore (python, node, .env, dist, __pycache__, .venv)
- Root .env.example (no real values)

Backend requirements:
- config.py: pydantic-settings class Settings with: decision_cutoff_local_time (default "09:00"), timezone (default "Europe/London"), data_dir (default "data"), cors_origins (list, default ["http://localhost:5173","http://localhost:3000"]), decision_start (date 2026-01-01), decision_end (date 2026-01-31).
- main.py: FastAPI app, CORS from settings, GET /api/health returning {"status":"ok"}.

Do NOT write Dockerfiles or any business logic in this milestone.

VERIFY (run and show output):
1. cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
2. cd backend && ruff check . 
3. cd backend && python -c "from app.main import app; print('import ok')"
4. cd backend && (uvicorn app.main:app --port 8000 &) ; sleep 3; curl -s localhost:8000/api/health ; kill %1
5. cd frontend && npm install && npm run build
```

### M1: Data fetch and profile (needs YOUR verified API facts)

```text
MILESTONE M1: Elexon data snapshot and data profile. Read: AGENTS.md, docs/DOMAIN_AND_ASSUMPTIONS.md, docs/PRD.md section FR5.

VERIFIED API FACTS (I checked these manually; use exactly these, do not guess others):
<<< PASTE HERE: base URL, FUELHH stream URL with working query parameters, WINDFOR stream URL with working query parameters, date format, max range per request, and a 3-row sample JSON response for each >>>

Task:
1. Create backend/scripts/fetch_data.py using httpx. It must:
   - fetch WINDFOR from 2025-12-28T00:00:00Z through 2026-02-01T00:00:00Z
   - fetch FUELHH from 2026-01-01T00:00:00Z through 2026-02-01T00:00:00Z, then keep only rows where fuelType == "WIND"
   - request in chunks (size per my verified facts), with retry (3 attempts, simple backoff) and a clear error on failure
   - normalise columns and write two parquet files:
     backend/data/actuals.parquet   columns: start_time (datetime64[ns, UTC]), actual_mw (float64)
     backend/data/forecasts.parquet columns: start_time (UTC), publish_time (UTC), forecast_mw (float64)
   - drop exact duplicate rows, never fill missing values, print row counts
2. Create backend/scripts/profile_data.py that loads both parquet files and prints:
   - row counts, min/max start_time and publish_time
   - number of distinct publish_time values and the typical gap between consecutive distinct publish times
   - min/max/median horizon in hours (start_time - publish_time)
   - number of duplicate (start_time, publish_time) pairs
   - number of 30-minute slots missing in actuals between 2026-01-01 and 2026-02-01
   - 5 sample rows of each table
3. Run both scripts for real and show the full output.
4. Append the findings to docs/DOMAIN_AND_ASSUMPTIONS.md under the heading "## Verified API facts", replacing the checklist there with real values.

Do NOT write selection or metrics code. After showing the profile output, STOP and wait for me.

VERIFY:
1. python backend/scripts/fetch_data.py
2. python backend/scripts/profile_data.py
3. ls -la backend/data
```

### M2: Core logic (use the reference code in section D)

```text
MILESTONE M2: core logic and tests. Read: AGENTS.md, docs/DOMAIN_AND_ASSUMPTIONS.md, docs/PRD.md.

I am giving you the reference implementation below. Place it EXACTLY as given into these files (fix only import or syntax errors, and tell me if you change anything):
- backend/app/services/forecast_selection.py
- backend/app/services/metrics.py
- backend/app/services/buffer.py
<<< PASTE the three code blocks from section D of OPENCODE_PROMPTS.md here >>>

Then write tests in backend/tests/:
- test_forecast_selection.py: (a) forecast published exactly at cutoff is included, one second after cutoff is excluded, one second before is eligible but the exact-cutoff one wins; (b) a slot with no eligible forecast yields missing_forecast True and NaN forecast; (c) result always has 48 rows for a January day; (d) naive selection picks the latest publish_time overall and differs from decision-time selection on the same fixture; (e) cutoff conversion for 2026-01-15 at 09:00 London gives 2026-01-14T09:00:00Z.
- test_metrics.py: fixture forecast [10,20,30], actual [8,25,30] gives errors [2,-5,0], bias -1.0, MAE 7/3, RMSE sqrt(29/3); missing values are excluded from metrics and counted; nMAE is None when mean actual is 0.
- test_buffer.py: fewer than 30 positive errors returns (None, count); with 40 known positive errors the P90 matches numpy.percentile.
Use small hand-built pandas DataFrames. No network, no parquet files.

VERIFY:
1. cd backend && pytest -q
2. cd backend && ruff check .
Show the full pytest output.
```

### M3: API

```text
MILESTONE M3: backend API. Read: AGENTS.md, docs/API_SPEC.md, docs/ARCHITECTURE.md.

Implement, matching docs/API_SPEC.md field names exactly:
- backend/app/services/data_store.py: loads backend/data/actuals.parquet and forecasts.parquet once at startup (lifespan), exposes the two DataFrames and the data range.
- backend/app/models/schemas.py: pydantic response models for every endpoint.
- backend/app/api/routes.py: GET /api/health, GET /api/config, GET /api/decision-forecast, GET /api/accuracy. Use the functions from services/forecast_selection.py, metrics.py, buffer.py. Do not reimplement their logic.
- Accuracy basis "decision": for every delivery day in range, run select_decision_forecast, join actuals on start_time, then compute overall, by_hour_of_day (Europe/London hour), error_histogram (20 equal-width bins), by_day, timeseries, naive_overall.
- by_horizon: use all forecasts (not only decision-time), join to actuals on start_time, bucket horizon hours into 0-6, 6-12, 12-24, 24-36, 36-48, 48+.
- Validation: 400 for dates outside configured range or bad cutoff format; 404 if no data.
- Suggested buffer in /api/decision-forecast must use only delivery days BEFORE the requested day (expanding window); if fewer than 30 positive-error slots, fall back to the full-period buffer and set buffer_basis to "full_period_fallback".
- Return JSON with NaN converted to null.

Write tests in backend/tests/test_api.py with FastAPI TestClient using the real parquet snapshot: health ok; decision-forecast for 2026-01-15 returns 48 rows; changing cutoff from 09:00 to 06:00 changes at least one publish_time; accuracy for the full range returns non-null mae_mw; bad date returns 400.

VERIFY:
1. cd backend && pytest -q
2. cd backend && ruff check .
3. start uvicorn and run: curl -s "localhost:8000/api/decision-forecast?date=2026-01-15" | head -c 600
4. curl -s "localhost:8000/api/accuracy?start=2026-01-02&end=2026-02-01" | head -c 600
```

### M4: Frontend, decision view

```text
MILESTONE M4: frontend decision view. Read: AGENTS.md, docs/PRD.md (FR1), docs/API_SPEC.md, docs/ARCHITECTURE.md.

Build in frontend/src:
- api/client.ts and types/api.ts: TypeScript types mirroring docs/API_SPEC.md exactly, typed fetch wrappers, base URL from import.meta.env.VITE_API_BASE_URL (default http://localhost:8000).
- hooks/useDecisionForecast.ts using TanStack Query.
- A QueryClientProvider and react-router with routes: "/" (DecisionView), "/accuracy" (placeholder text), "/methodology" (placeholder text). Top nav links between them.
- pages/DecisionView.tsx: delivery date input (min/max from /api/config), cutoff time input (default from /api/config), and:
  - Recharts line chart, 48 points: decision-time forecast and actual (actual may be null, render gaps), x axis in Europe/London time HH:mm, y axis in MW with axis label.
  - Summary strip: latest publish time used, MAE, bias, suggested buffer MW with its buffer_basis.
  - Data-quality banner shown when n_missing_forecast or n_missing_actual > 0.
  - Table: start time, forecast, publish time, horizon hours, actual, error.
  - Loading, error, and empty states.
- Put date and cutoff in URL query params so links are shareable.
Do NOT build the accuracy page yet. Keep CSS in one plain CSS file.

VERIFY:
1. cd frontend && npm run build
2. cd frontend && npm run lint
3. Start backend and frontend, then curl -s localhost:5173 | head -5 and tell me which page and route I should open to eyeball the chart.
```

### M5: Frontend, accuracy dashboard

```text
MILESTONE M5: accuracy dashboard. Read: AGENTS.md, docs/PRD.md (FR2, FR2b, FR2c), docs/API_SPEC.md.

Build pages/Accuracy.tsx and components:
- Date range inputs (default full range from /api/config), basis toggle (decision / all_horizons), cutoff input.
- KpiCards: MAE, RMSE, bias, nMAE %, P90 abs error, n, missing counts. Units visible on every number.
- ForecastChart reuse: forecast vs actual over the whole range.
- ErrorHistogram (bar chart from error_histogram).
- HourOfDayChart (MAE and bias by hour).
- HorizonChart (MAE by horizon bucket).
- LeakageComparison: shows decision-time MAE next to naive MAE (naive_overall) and a per-day line chart using by_day, with the caption "Naive numbers look better because they use forecasts the buyer did not yet have. Not usable for decisions."
- Loading, error, empty states.
Expose, in a small "Numbers for findings" section at the bottom, the raw values needed for docs/FINDINGS.md (MAE by horizon bucket, worst 3 hours by MAE, bias, share of slots over-forecast if the API provides it; if not, say it is missing, do not invent it). Do NOT write conclusions or edit docs/FINDINGS.md.

VERIFY:
1. cd frontend && npm run build && npm run lint
2. Show the component file list.
```

### M6: Methodology page and decision aid polish

```text
MILESTONE M6: methodology page and decision aid. Read: AGENTS.md, docs/PRD.md (FR3, FR4), docs/DOMAIN_AND_ASSUMPTIONS.md.

1. pages/Methodology.tsx (static content): data sources (FUELHH WIND, WINDFOR only), the cutoff assumption stated as a configurable default read from /api/config, forecast selection rule in one paragraph, metric formulas (bias, MAE, RMSE, nMAE, percentiles), buffer definition (P90 of positive errors only, expanding window, 30-slot minimum), limitations list (no demand data; cutoff is an assumption; wind only; national level only).
2. In DecisionView add a "conservative wind" line (forecast minus suggested buffer, floored at 0) as a dashed series, with a legend entry and tooltip text "indicative, not advice".
Keep wording plain for a trader.

VERIFY:
1. cd frontend && npm run build && npm run lint
```

### M7: Docker and deployment files

```text
MILESTONE M7: Docker and deploy config. Read: AGENTS.md, docs/DEPLOYMENT.md.

Create:
- backend/Dockerfile: python:3.12-slim, copy requirements, pip install, copy app, scripts and data, CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} (use shell form so PORT expands), non-root user.
- frontend/Dockerfile: multi-stage; node:20 build with ARG VITE_API_BASE_URL, then nginx:alpine serving dist with an nginx.conf that falls back to /index.html. Expose 80.
- docker-compose.yml: backend on 8000, frontend on 3000 (map to container 80), build arg VITE_API_BASE_URL=http://localhost:8000.
- .dockerignore files for both.
- heroku.yml at the root building backend/Dockerfile as the web process.
- frontend/vercel.json with an SPA rewrite to /index.html.
Do NOT deploy anything and do NOT run any heroku or vercel command.

VERIFY:
1. docker compose build
2. docker compose up -d && sleep 8 && curl -s localhost:8000/api/health && curl -sI localhost:3000 | head -1 ; docker compose down
If Docker is not installed in this environment, say so and skip 1 and 2.
```

### M8: README and anonymity sweep

```text
MILESTONE M8: README and cleanup. Read: AGENTS.md, docs/PRD.md, docs/DOMAIN_AND_ASSUMPTIONS.md.

1. Write README.md with sections: overview (2-3 lines), live links (placeholders "LIVE_APP_URL" and "API_URL" for me to fill), key assumption (cutoff default and delivery-day interpretation, stated as an assumption), repository structure (every top-level directory and important file with one line each), run with Docker, run without Docker (backend and frontend commands), data (sources, snapshot, how to regenerate), testing, and an explicit AI-tools disclosure stating that AI coding assistants were used to help build this project and that the code was reviewed by the author.
2. Anonymity sweep: search the whole repo (excluding node_modules, .venv, .git) for: my real name, any email address, "http" links that are not Elexon, Docker, Vercel, Heroku, library docs, or localhost, and package.json "author" / pyproject metadata. Report every hit and fix those that identify a person or employer. I will tell you my name to search for: <<< NAME >>>.
3. Do not edit docs/FINDINGS.md.

VERIFY:
1. Show the final README.
2. Show the grep commands and their results.
3. cd backend && pytest -q && cd ../frontend && npm run build
```

---

## C. Recovery prompts

**Context was lost or you resumed a session**
```text
Read AGENTS.md and PROGRESS.md. Then run `git status` and `git log --oneline -10`. Tell me in 5 lines: which milestone is finished, what is half-done, and what the next single step is. Do not change any file yet.
```

**Model is looping on a failing test**
```text
Stop editing. Run the failing command once and paste the full error. Then list the 3 most likely causes ranked by probability and the one-line check that would confirm each. Do not change code until I pick one.
```

**Model changed something it should not have**
```text
Run `git diff --stat`. List every file you changed that is outside the current milestone's scope. For each, explain why, then revert it with `git checkout -- <file>` unless I say otherwise.
```

**Model claims it is done but you doubt it**
```text
Re-run every VERIFY command from the milestone and paste the raw output without summarising. Then list every requirement bullet from the milestone prompt and mark each: implemented (file and line), partly implemented, or missing.
```

**Review pass at the end**
```text
Review the whole repo against docs/PRD.md acceptance criteria AC1 to AC8. For each, state pass or fail with evidence (file, test name, or command output). Do not fix anything yet; just report.
```

---

## D. Reference implementations (paste into the M2 prompt)

### backend/app/services/forecast_selection.py

```python
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

DEFAULT_TZ = "Europe/London"


def cutoff_utc_for(delivery_date: date, cutoff_local: time, tz: str = DEFAULT_TZ) -> datetime:
    """Cutoff = D-1 at cutoff_local in local time, converted to UTC."""
    local = datetime.combine(delivery_date - timedelta(days=1), cutoff_local, tzinfo=ZoneInfo(tz))
    return local.astimezone(timezone.utc)


def expected_slots(delivery_date: date, tz: str = DEFAULT_TZ) -> pd.DatetimeIndex:
    """All 30-minute slot start times (UTC) for the local delivery day."""
    zone = ZoneInfo(tz)
    start = datetime.combine(delivery_date, time(0, 0), tzinfo=zone).astimezone(timezone.utc)
    end = datetime.combine(delivery_date + timedelta(days=1), time(0, 0), tzinfo=zone).astimezone(
        timezone.utc
    )
    return pd.date_range(start=start, end=end, freq="30min", inclusive="left")


def _select_latest(
    forecasts: pd.DataFrame, slots: pd.DatetimeIndex, cutoff: datetime | None
) -> pd.DataFrame:
    """Latest publish_time per slot, optionally restricted to publish_time <= cutoff.

    forecasts columns: start_time (UTC), publish_time (UTC), forecast_mw.
    """
    eligible = forecasts[forecasts["start_time"].isin(slots)]
    if cutoff is not None:
        eligible = eligible[eligible["publish_time"] <= cutoff]
    chosen = (
        eligible.sort_values(["start_time", "publish_time"])
        .drop_duplicates(subset="start_time", keep="last")
        .set_index("start_time")
    )
    out = chosen.reindex(slots)
    out.index.name = "start_time"
    out["missing_forecast"] = out["forecast_mw"].isna()
    out["horizon_hours"] = (out.index.to_series() - out["publish_time"]).dt.total_seconds() / 3600
    return out.reset_index()


def select_decision_forecast(
    forecasts: pd.DataFrame,
    delivery_date: date,
    cutoff_local: time,
    tz: str = DEFAULT_TZ,
) -> pd.DataFrame:
    """Forecast the buyer actually had: latest publish_time <= cutoff, no look-ahead."""
    cutoff = cutoff_utc_for(delivery_date, cutoff_local, tz)
    return _select_latest(forecasts, expected_slots(delivery_date, tz), cutoff)


def select_naive_forecast(
    forecasts: pd.DataFrame, delivery_date: date, tz: str = DEFAULT_TZ
) -> pd.DataFrame:
    """Comparison only: latest forecast ever published, ignoring the cutoff (uses leaked info)."""
    return _select_latest(forecasts, expected_slots(delivery_date, tz), None)
```

### backend/app/services/metrics.py

```python
from __future__ import annotations

import numpy as np
import pandas as pd


def summarize(df: pd.DataFrame) -> dict:
    """df needs columns forecast_mw and actual_mw. Error = forecast - actual.

    Slots missing either value are excluded from metrics and counted.
    """
    n_missing_forecast = int(df["forecast_mw"].isna().sum())
    n_missing_actual = int(df["actual_mw"].isna().sum())
    valid = df.dropna(subset=["forecast_mw", "actual_mw"])
    base = {
        "n": int(len(valid)),
        "n_missing_forecast": n_missing_forecast,
        "n_missing_actual": n_missing_actual,
    }
    if valid.empty:
        return {
            **base,
            "bias_mw": None,
            "mae_mw": None,
            "rmse_mw": None,
            "nmae_pct": None,
            "p50_abs_error_mw": None,
            "p90_abs_error_mw": None,
            "p95_abs_error_mw": None,
        }
    err = valid["forecast_mw"] - valid["actual_mw"]
    abs_err = err.abs()
    mean_actual = float(valid["actual_mw"].mean())
    mae = float(abs_err.mean())
    return {
        **base,
        "bias_mw": float(err.mean()),
        "mae_mw": mae,
        "rmse_mw": float(np.sqrt((err**2).mean())),
        "nmae_pct": (mae / mean_actual * 100) if mean_actual > 0 else None,
        "p50_abs_error_mw": float(np.percentile(abs_err, 50)),
        "p90_abs_error_mw": float(np.percentile(abs_err, 90)),
        "p95_abs_error_mw": float(np.percentile(abs_err, 95)),
    }
```

### backend/app/services/buffer.py

```python
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_POSITIVE_SAMPLES = 30


def over_forecast_buffer(
    errors: pd.Series, q: float = 90.0, min_n: int = MIN_POSITIVE_SAMPLES
) -> tuple[float | None, int]:
    """P-q of errors where error > 0 (forecast above actual).

    errors = forecast - actual. Returns (buffer_mw or None if too few samples, count of positives).
    """
    pos = errors.dropna()
    pos = pos[pos > 0]
    if len(pos) < min_n:
        return None, int(len(pos))
    return float(np.percentile(pos, q)), int(len(pos))
```

---

## E. Things to check yourself because the model will probably get them wrong
- Timestamps stay tz-aware UTC everywhere (no naive datetimes after loading parquet).
- Forecast chosen for each slot really has `publish_time <= cutoff` (spot-check one day by hand against the raw parquet).
- The frontend x-axis shows London time, not UTC.
- NaN never reaches the JSON (it breaks the frontend).
- `git log` shows only the neutral author.
- Open the deployed URLs in incognito before submitting.