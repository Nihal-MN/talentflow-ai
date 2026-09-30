# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **International resume parsing** — dotted `DD.MM.YYYY` / `MM.YYYY` dates,
  German/French/Spanish section headers (`BERUFSERFAHRUNG`, `AUSBILDUNG`,
  `KENNTNISSE`, …) and dotted degree abbreviations (`B.Sc.`, `M.Sc.`,
  `Diplom`); contact-line locations preferred over job-title lines.
- **Skill taxonomy extensions** — `bash`, `swift`, `objective-c`, `dart`,
  `scala`, `flutter`, `android`, `firebase`, `databricks`, `ansible`,
  `pulumi`, `mlops`, `zendesk`, `freshdesk`; cloud aliases (`s3`, `ec2`,
  `ecs`, `eks`, `gke`, `aks`); new `iac` and `mobile` families
  (`backend/tests/test_skills.py`).
- **Pagination completeness** — `offset` on `/applications`; **`X-Total-Count`**
  response header on `/jobs`, `/candidates` and `/applications` (exposed via
  CORS); boundary tests in `backend/tests/test_pagination.py`.
- **Example data** — career-changer and non-Western date-format resumes plus a
  support team-lead JD, and `scripts/verify_examples.sh` which uploads every
  example file to a running API and prints an extraction summary.
- **`docs/API.md` cookbook** — verified, copy-paste `curl` examples for the
  full workflow (job → resume → match → pipeline → screening).
- **`docs/ACCESSIBILITY.md`** — axe-core audit across all 9 pages, findings
  and fixes (contrast, labels, heading order).

### Fixed

- Color contrast across the UI (muted text now meets AA on its actual
  surface, per-surface rather than globally).
- Accessible names for the resume and JD file inputs.
- Heading order on the matching page.
- **Education parsing** — combined ``Degree - Institution (years)`` lines are
  split into separate `degree` / `institution` fields (each a verbatim
  substring of the resume line) instead of duplicating the whole line into
  both fields.
- **Education evidence** — match evidence for education is quoted in the
  resume's own formatting when the string occurs in the stored resume text;
  all resume-claiming evidence snippets across the seeded data are now
  verbatim-traceable to the stored resume sources (checked programmatically:
  233/233 across all 40 candidate×job pairs).
- **Markdown job descriptions** — headings and ``**bold**`` labels parse
  correctly (correct title/company on the shipped Markdown example JD; the
  responsibilities section no longer leaks into requirements).
- **`alembic check`** now reports "No new upgrade operations detected" on
  PostgreSQL — the pgvector HNSW index (created via raw DDL, intentionally
  absent from the ORM metadata) is excluded from autogenerate comparison.

## [0.1.0] - 2026-09-29

First public release. TalentFlow AI is an AI-native hiring pipeline with
structured talent data, explainable candidate matching and
recruiter-in-the-loop workflows. It runs fully without an API key (deterministic
mock AI, labeled everywhere) and uses the OpenAI API with structured outputs
when a key is configured.

### Added

- **Jobs** — create from pasted text or uploaded JD files (PDF/DOCX/TXT);
  requirements extracted into must-have/preferred with skills, minimum years,
  education, location and domain signals; per-record AI provenance
  (`extraction_method`: `mock`/`openai`).
- **Candidates** — multi-file resume upload with validated structured profiles:
  experience timeline, education, certifications, canonicalized skills (each
  with an evidence line), computed years of experience; notes and tags.
- **Explainable matching** — requirement-by-requirement evaluation
  (`met`/`partial`/`missing`/`unknown`/`advisory`) with written reasons, quoted
  resume evidence, related-skill partial credit, coverage counts and a
  composite score whose formula is rendered next to it
  (`0.60·must_have + 0.20·preferred + 0.10·experience + 0.10·domain`,
  re-normalized over present components). Deterministic: same input, same
  output; engine version recorded per result.
- **Semantic search** — embeddings per text chunk; pgvector (HNSW cosine index)
  on PostgreSQL with an in-process fallback on SQLite; similarity is a
  supporting signal that can never override a deterministic miss.
- **Hiring pipeline** — NEW → SCREENING → SHORTLISTED → INTERVIEW → OFFER →
  HIRED with a REJECTED off-ramp; append-only stage-event audit trail;
  pipeline board.
- **Screening questions** — generated per application from match results
  (strengths, gap probes, behavioral), category-restricted schema, each with a
  rationale; human-review framing throughout.
- **System health** — live database and AI-configuration report; never exposes
  key material.
- **Provider architecture** — one interface, two implementations: OpenAI
  (Responses API, structured outputs; `text-embedding-3-small`) and a
  deterministic offline mock (rule-based extraction, hashed-ngram embeddings).
- **Zero-config demo** — `docker compose up --build` + `python -m app.seed`
  loads 4 synthetic jobs and 10 synthetic candidates ingested through the real
  pipeline from PDF/DOCX/TXT files.
- **Documentation** — README, docs/ARCHITECTURE.md, docs/AI_DESIGN.md,
  docs/MATCHING.md, docs/API.md, docs/TESTING.md, RESPONSIBLE_AI.md,
  SECURITY.md, ADRs 0001–0004, demo screenshots.
- **Quality** — 95 backend tests (91% coverage, PostgreSQL+pgvector integration
  included) + 18 frontend tests; ruff/ESLint/strict TypeScript enforced; CI on
  GitHub Actions (PostgreSQL service container, Docker builds).

### Security

- No authentication in the demo — documented as a pre-deployment requirement
  (see SECURITY.md). No secrets in the repository; `.env` git-ignored; upload
  validation with size caps and parser isolation; CORS allow-list; structured,
  information-bounded errors.

### Known limitations

- See the "Known limitations" section in the [README](README.md#known-limitations).
  Highlights: no auth, mock extractor is English-centric, no OCR for scanned
  PDFs, single-process deployment profile.

[Unreleased]: https://github.com/Nihal-MN/talentflow-ai/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Nihal-MN/talentflow-ai/releases/tag/v0.1.0
