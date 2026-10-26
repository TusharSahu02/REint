# Deployment

Everything here is free-tier only. Heroku is not: free dynos were discontinued in
November 2022 and the cheapest paid dyno is $5/month (Eco, sleeps after 30 min), so it is
not part of this plan.

## What the app needs

- Backend: FastAPI, reads a committed 128 KB snapshot (no database, no object store, no
  external API at runtime).
- Frontend: static Vite build.
- One env var on the backend (`CORS_ORIGINS`, JSON list) and one on the frontend
  (`VITE_API_BASE_URL`, the backend's public URL).

## Option A (recommended): Cloudflare Pages + Google Cloud Run

No cold-start penalty of minutes, no sleeping service, both inside free allowances.
Cloud Run needs a credit card on file (it is not charged beyond the free tier, and
alerts can be set to cap spend).

Frontend on Cloudflare Pages
1. New project, connect the repo, build settings: framework Vite, build command
   `npm run build`, output directory `dist`, root directory `frontend`.
2. Environment variable: `VITE_API_BASE_URL=https://<service>-<hash>.run.app`.
3. SPA fallback: Cloudflare Pages serves `index.html` for unknown paths automatically
   for Vite projects; if not, add `frontend/public/_redirects` with `/* /index.html 200`.

Backend on Google Cloud Run
```bash
cd backend
gcloud run deploy wind-forecast-monitor-api \
  --source . --region europe-west2 --allow-unauthenticated \
  --set-env-vars CORS_ORIGINS='["https://<your-pages-domain>"]'
```
`backend/Dockerfile` already binds `$PORT`, which Cloud Run sets.

Free allowances: 2M requests/month, 1 vCPU and 0.5 GB RAM always-free, 1 GB egress.

## Option B: Vercel + Render (no card required)

Frontend on Vercel
1. New project, root directory `frontend`, framework preset Vite (build `npm run build`,
   output `dist`). `frontend/vercel.json` already adds the SPA rewrite.
2. Environment variable: `VITE_API_BASE_URL=https://<api>.onrender.com`.

Backend on Render
1. New Web Service from this repo; `render.yaml` in the repo root is picked up
   automatically (Blueprint), or configure manually: runtime Docker, dockerfile
   `./backend/Dockerfile`, context `./backend`, plan Free, health check `/api/health`.
2. Set `CORS_ORIGINS` to `["https://<your-app>.vercel.app"]` (JSON list).

Free allowances: 750 instance-hours/month per workspace, 5 GB bandwidth/month.
Caveat: free services spin down after 15 minutes idle and take about a minute to wake,
so the first request after a break can look slow.

## Option C: one service for both (fewest moving parts)

Serve the built SPA from FastAPI itself and deploy a single container. One URL, no
CORS, no second provider. Good for a reviewer who only needs one link.

```bash
cd frontend && npm run build && cd ..
# copy frontend/dist into backend/static, mount it in app/main.py, then:
cd backend && gcloud run deploy wind-forecast-monitor --source . --allow-unauthenticated
```
Use the same free tier as Option A (Cloud Run) or a Render free web service.

## Other free options, ranked

| Platform | Free tier | Catch |
|---|---|---|
| Google Cloud Run | 2M req/mo, 1 vCPU + 0.5 GB always-free | card required |
| Render | 750 instance-hours/mo, 512 MB | sleeps 15 min, ~1 min wake, 5 GB bandwidth |
| Koyeb | 1 free web service, 512 MB, scales to zero after 1 h | card required since Feb 2026 ($29 hold) |
| Cloudflare Pages | free static, unlimited bandwidth, 500 builds/mo | no Python backend (Workers only) |
| Vercel | free static, 100 GB transfer, 1M CDN requests | Hobby is non-commercial; Python functions have cold starts and 250 MB limits |
| Fly.io / Railway | no permanent free tier | trial credit only |
| Heroku | none | cheapest is $5/mo |

Note on Vercel hosting the API: it works (FastAPI as a Python function, data is only
128 KB), but every cold start re-imports pandas and the Hobby plan is non-commercial, so
a normal container host is the better fit.

## Verification checklist

- [ ] Open the frontend URL in incognito: charts load with real data.
- [ ] `https://<api>/api/health` returns 200.
- [ ] `CORS_ORIGINS` contains the frontend origin only, and the browser console shows no
      CORS errors.
- [ ] Deep link (for example `/accuracy`) loads, proving the SPA rewrite works.
- [ ] README links updated with the deployed URLs.
