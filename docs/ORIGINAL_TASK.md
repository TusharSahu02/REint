# Original Task (verbatim summary of the brief)

Role: product developer building a customised software product for a UK energy utility. Present/pitch to the client and explain design/implementation to an internal tech lead.

Client team buys power from the UK **day-ahead market**. They need to know how much power must be procured beyond renewable (wind) generation. Wind is weather-dependent and day-ahead decisions are made one day before delivery, so they rely on forecasts.

The web app must let them:
1. Clearly understand the **latest renewable generation forecasts available when they need to make decisions** on buying from the day-ahead market.
2. **Evaluate forecast accuracy quantitatively** so decisions can account for the quantified error.

Scope limits: national-level wind actuals and forecasts from Elexon only, no other data.

- Actuals: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream — use `fuelType` = `WIND`. Fields: `startTime` (30-min resolution target time), `generation`.
- Forecasts: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream — fields: `startTime`, `publishTime` (when forecast was created), `generation`.
- Consider data relevant only for purchase decisions made in **January 2026**.

Build: React frontend, Python backend, Docker, deploy on Vercel or Heroku. AI tools allowed but must be mentioned in README. Max 16 hours.

Deliverables:
- Unlisted YouTube video, max 10 min total. Part 1 (max 5 min): customer pitch of the pilot, aim to impress. Part 2 (max 5 min): tech lead review: architecture, design, analysis, code base, key development practices.
- Public GitHub repo with an anonymous name (random string). README with: files/directories, how to start the app, link to the deployed app.
- Submit all details via the form. Open every submitted URL in incognito to verify access.
