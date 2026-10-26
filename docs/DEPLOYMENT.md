# Deployment

## Local
`docker compose up --build` → backend http://localhost:8000 (docs at /docs), frontend http://localhost:3000.

## Backend: Heroku (container)
- `backend/Dockerfile` must bind to `$PORT` (e.g. `CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`).
- Root `heroku.yml`:
```yaml
build:
  docker:
    web: backend/Dockerfile
```
- Steps: `heroku create <random-name>` → `heroku stack:set container` → set config vars (`CORS_ORIGINS`, `DECISION_CUTOFF_LOCAL_TIME`) → `git push heroku main`.
- Note: Heroku has no free tier; basic dyno is paid. Snapshot data is baked into the image, so no external storage needed.

## Frontend: Vercel
- Root directory: `frontend`. Framework: Vite. Build `npm run build`, output `dist`.
- Env var: `VITE_API_BASE_URL=https://<heroku-app>.herokuapp.com`.
- Add SPA rewrite so client-side routes work (`vercel.json` rewrite to `/index.html`).

## Verification checklist
- [ ] Open Vercel URL in incognito: charts load with real data.
- [ ] Backend `/api/health` public.
- [ ] CORS allows the Vercel origin only.
- [ ] README links updated.
