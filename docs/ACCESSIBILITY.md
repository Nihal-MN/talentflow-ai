# Accessibility — TalentFlow AI

An honest, reproducible audit of the UI. **This is not a formal WCAG
certification** — it is a documented pass with a real tool, real results, and
a clearly stated scope.

## Method

- **Tool:** [axe-core](https://github.com/dequelabs/axe-core) 4.10.2 (Deque),
  default ruleset (WCAG 2.1 A/AA + best-practice rules).
- **How:** injected into a real Chrome session via the Chrome DevTools
  Protocol against the **Docker stack with the synthetic seed data**
  (`docker compose up --build -d && docker compose exec api python -m app.seed`),
  viewport 1280×900, every page loaded with live data.
- **Pages covered (all 9):** dashboard, jobs, job detail, candidates,
  candidate detail, matching, pipeline, screening, system health.

## Findings before fixes (30 Sep 2026)

| Rule | Impact | Result |
|---|---|---|
| `color-contrast` | serious | **71 nodes across 8 pages** — muted text (`slate-400`, ≈2.6:1) on light surfaces, below the 4.5:1 ratio for normal text |
| `label` | critical | the resume file input on **/candidates** had no accessible name |
| `heading-order` | moderate | **/matching** jumped from the page `h1` to card `h3` (skipped `h2`) |

## Fixes applied

1. **Contrast** — muted text darkened on light surfaces (`text-slate-400` →
   `text-slate-500`, 53 occurrences), plus targeted `slate-600` for job-title
   lines and `slate-700` for code chips sitting on tinted backgrounds.
2. **Dark surfaces handled in the correct direction** — text on the dark
   sidebar (`bg-slate-900`) stayed/returned to `slate-400`, which passes AA
   there (`slate-500` would be too dim). Contrast fixes are per-surface, not
   global.
3. **Accessible names** — `aria-label` added to the resume upload input
   (candidates) and the JD upload input (jobs).
4. **Heading order** — match-card candidate name changed from `h3` to `h2`,
   which is valid beneath each page's `h1`.

## Verification after fixes

The exact same audit was re-run after each change: **0 axe violations across
all 9 pages** (the final straggler — a timestamp line on /screening — was
fixed and re-verified).

## What this does NOT cover (honest scope)

- **No screen-reader walkthrough** (VoiceOver/NVDA) — recommended as the next
  step; axe catches maybe half the issues a real reader finds.
- **No zoom/reflow (200%) or reduced-motion pass.**
- **No formal WCAG conformance claim** — say "audited with axe-core, clean",
  not "WCAG compliant".
- Mobile-viewport spot checks only (the UI is desktop-first, as documented).

## Re-running the audit

1. Start the stack with seed data (`docker compose up --build -d && docker
   compose exec api python -m app.seed`).
2. Serve axe-core locally (or fetch from a CDN) and inject it in a browser
   session, then evaluate `axe.run(document)` per page — the exact method used
   for this audit.
3. A CI-friendly regression version (vitest + `jest-axe` on key components)
   is a suggested follow-up for contributors.
