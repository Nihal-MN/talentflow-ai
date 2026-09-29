# Roadmap

Direction, not promises. This is a demo/portfolio-scale project; items move
when they move. Ground rules stay fixed: **no opaque scores, no protected
characteristics, no fake AI** (mock output is always labeled).

## Current — v0.1.0 (shipped)

Working today, verified by tests and an end-to-end acceptance run:

- Hiring pipeline: NEW → SCREENING → SHORTLISTED → INTERVIEW → OFFER → HIRED
  (+ REJECTED), with an append-only stage-event audit trail.
- Explainable, deterministic-first candidate matching: per-requirement
  `met`/`partial`/`missing` with quoted resume evidence and a published
  scoring formula.
- Structured resume + JD parsing (PDF/DOCX/TXT) with validated schemas and
  per-record AI provenance (`mock` / `openai`).
- Semantic search over candidate/JD text (pgvector on PostgreSQL; in-process
  fallback on SQLite).
- Screening-question generation grounded in match results, each with a
  rationale.
- Notes, tags, system health report; zero-config Docker demo; hermetic test
  suites; CI on GitHub Actions.

## Next — high priority

- **Authentication and multi-tenant workspaces** — the service layer is the
  single mutation choke-point, so an auth wrapper lands in one place.
- **Pagination and filtering** on candidate/job collections (currently
  unbounded — fine for demo scale, not beyond).
- **Accessibility audit** — keyboard flows, focus states and contrast
  verified across every page, with fixes and a documented checklist.
- **OpenAI reranking evaluation harness** — an offline eval set to measure and
  document extraction quality of the live provider, so provider quality is a
  measured claim rather than a hope.
- **CSV export** of candidates, applications and match results.

## Future — under consideration

- Interview scheduling with structured interview scorecards.
- ATS connectors (e.g. Greenhouse/Lever) and email/calendar integrations.
- Analytics dashboards (funnel conversion, time-in-stage) built only on
  non-protected data.
- Deployment templates (production compose behind a reverse proxy with auth,
  or a small managed-host walkthrough).
- MCP (Model Context Protocol) server exposing the API to agent tooling.
- Localization of the UI (English-only today).
- OCR for scanned/image resumes.

## Explicit non-goals

- Autonomous hiring decisions. TalentFlow is decision support; a human decides,
  always (see [RESPONSIBLE_AI.md](RESPONSIBLE_AI.md)).
- Any use of protected characteristics in ranking, now or later.
- Presenting mock/demo output as live AI output.
