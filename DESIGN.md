# Design

## Theme

Light, always: the buyer reads this at the desk mid-morning under office light. Paper-like, ink-dark text, one glaucous storm-blue where "forecast" lives. No dark mode.

## Register

Product. Data is the hero; chrome is hairlines and whitespace. Linear-class restraint: no gradient anything, no card soup.

## Color (OKLCH, tinted, never #000/#fff)

| Token | Value | Use |
|---|---|---|
| --bg | oklch(0.963 0.006 245) | page background |
| --panel | oklch(0.994 0.004 245) | panels, topbar, chart surface |
| --panel2 | oklch(0.949 0.008 245) | toolbar, inset zones |
| --ink | oklch(0.27 0.028 255) | body text, headings |
| --muted | oklch(0.50 0.026 252) | labels, captions |
| --border | oklch(0.90 0.013 245) | hairlines |
| --accent | oklch(0.55 0.110 240) | forecast line, primary/active nav, focus rings |
| --accent-strong | oklch(0.47 0.110 240) | hover |
| --actual | oklch(0.63 0.130 65) | actuals line |
| --error | oklch(0.58 0.150 35) | bias/error bars |
| --warn-bg | oklch(0.965 0.045 88) | banner background |
| --warn-border | oklch(0.78 0.110 80) | banner border |
| --warn-ink | oklch(0.44 0.090 70) | banner text |
| --naive | oklch(0.72 0.022 250) | naive comparison (deliberately colourless: not usable for decisions) |

Chart colour-blind safety: forecast (blue, L .55) vs actual (amber, L .63) differ in lightness as well as hue; bias bars get the lightest L in their chart. Legends always shown.

## Typography

System UI stack (`Inter` first when installed). Base 14px, data/tables 13px, micro-labels 11px uppercase tracked. Scale step ~1.12. All numerics `font-variant-numeric: tabular-nums`. KPI values 28px/600; section titles 15px/650; page h1 21px/650.

## Spacing

Page column max 1080px. Section rhythm: 28px between blocks, 12/16 inside panels. Toolbar is its own band (--panel2), controls inline.

## Components

- Section: hairline-topped block, no box, for prose/columns. Panel: bordered 12px-radius box for charts and tables.
- Stat strip: flex row, hairline dividers, no boxes (replaces KPI card grid).
- Buttons/inputs: 8px radius, hairline border, --bg fill; focus = 2px accent ring offset 2px.
- State: hover, focus, disabled (0.55 opacity), error, flagged-row tint; all standardized.
- Motion: 150ms ease-out on hover/focus/background transitions only; `prefers-reduced-motion` kills it. No page-load choreography.
- Loading: quiet pulsing placeholder row, not spinners.
- Naive/leakage zone: neutral "not usable" pill, amber banner vocabulary reserved for the cutoff warning; never side-stripes.
- Methodology page: editorial Q&A, not a panel stack. Numbered questions (01..) in accent, 72ch measure, hairline rule between items, definition list for metric terms, lede paragraph. No boxes on this page.
