# Milestones (target total: under 16 hours)

Check items off as done. One milestone at a time.

## M0 Setup (0.5h)
- [x] Monorepo scaffold: backend (FastAPI), frontend (Vite React TS), docker-compose
- [x] ruff, pytest, eslint/prettier configured
- [x] CI-less but `make`-style commands documented in README

## M1 Data discovery and snapshot (2h)
- [x] Read live Elexon docs; fill "Verified API facts" in DOMAIN_AND_ASSUMPTIONS.md (parameter names, formats, range limits)
- [x] `scripts/fetch_data.py`: WINDFOR from ~28 Dec 2025, FUELHH (WIND) 1 Jan to 1 Feb 2026, chunked by date, saved to parquet
- [x] Data profile script: print raw samples and report publish frequency, horizon range, duplicates, gaps, row counts
- [x] STOP: show findings to the human owner before M2
- [x] Commit snapshot

## M2 Core logic (2.5h)
- [x] `forecast_selection.py` + tests (cutoff boundary: publishTime == cutoff included, +1s excluded; slots with no forecast)
- [x] `metrics.py` + tests with hand-computed fixture
- [x] `buffer.py` expanding window (P90 of positive errors only) + tests
- [x] Naive (no-cutoff) selection + test showing it differs from decision-time selection

## M3 API (1.5h)
- [x] Config, data store, routes per API_SPEC, pydantic models
- [x] API tests via TestClient
- [x] CORS via env

## M4 Frontend: Decision view (2h)
- [x] Layout, date picker, cutoff control, ForecastChart, table, data-quality banner

## M5 Frontend: Accuracy dashboard (2h)
- [x] KPI cards, time series, histogram, hour-of-day, horizon charts, basis toggle
- [x] Leakage comparison card/chart (decision-time vs naive)
- [x] Findings-supporting numbers exposed (human writes FINDINGS.md)

## M6 Decision aid and Methodology (1h)
- [x] Buffer + conservative wind line, methodology page

## M7 Docker and deploy (1.5h)
- [ ] Dockerfiles, compose, heroku.yml, Vercel config; deployed and verified in incognito (configs done, deploy pending)

## M8 README and polish (1h)
- [x] README (structure, run steps, live link, cutoff assumption and rationale, AI disclosure; anonymous, no personal identifiers)
- [x] Anonymity sweep: grep for names, employer, emails; set neutral git author
- [x] Empty/error/loading states, number formatting, responsive check (laptop-first layout verified in browser)
