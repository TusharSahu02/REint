# Product

## Register

product

## Users

UK day-ahead power buyers on an energy trading desk. Strong domain experts, not data experts. They check the desktop app at the desk in the morning (cutoff is 09:00 Europe/London D-1), under normal office light, to decide what to buy for tomorrow and to review how wrong the forecast was yesterday. Primary tasks: (1) pick a delivery date and see the forecaster's numbers plus a buffer, (2) review national-level forecast error (how often, how big, in which hours), (3) understand methodology to be able to say exactly what the numbers mean.

## Product Purpose

Show the wind generation forecast that was actually available when the buying decision had to be made (no look-ahead leakage), and quantify forecast accuracy against actual generation (Elexon BMRS data: WINDFOR forecasts, FUELHH actuals). Success: buyer can state, before cutoff, "the forecast says X, actuals usually run ~2 GW higher, buffer per P90 is Y" and anyone can audit how that number was computed just by reading the app.

## Brand Personality

Calm, precise, credible. Modern B2B SaaS polish (Linear/Notion class) without template smell. Data is the hero; chrome stays quiet. Numbers are big and tabular; copy is short and definitive.

## Anti-references

- Generic SaaS admin: interlock grey cards, icon+title+text card grids, gradient hero-metric tiles, decorative glassmorphism, side-stripe callouts.
- Bloomberg-terminal cosplay: black void with neon green, 20px font tables, dilbert chrome.
- Enterprise portal: dense toolbars, modal-heavy flows, clutcher headers.

## Design Principles

- Data first: every pixel of chrome must justify itself against the forecast/error numbers.
- Provenance visible: cutoff time, publish time, sample size, and basis are always on screen. A number you cannot trace is a lie.
- Leakage honesty: the app deliberately shows the naive comparison; its "not usable for decisions" nature must be visible at a glance, not buried.
- Calm precision: one accent carries meaning (error/bias), the rest is neutral; color-blind-safe chart colors.
- Expert compression: no explanations of basics; domain language (slot, cutoff, D-1, P90) as-is.

## Accessibility & Inclusion

- WCAG AA contrast minimum throughout.
- Chart color pairs distinguishable without hue alone (lightness/shape redundancy).
- Respect prefers-reduced-motion.
