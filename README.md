# TalentFlow AI

**Open-source AI-native hiring pipeline with structured talent data, explainable candidate matching, semantic search and recruiter-in-the-loop workflows.**

[![CI](https://github.com/Nihal-MN/talentflow-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Nihal-MN/talentflow-ai/actions/workflows/ci.yml)
![Backend tests: 94 passing on PostgreSQL](https://img.shields.io/badge/backend_tests-95_passing_on_PostgreSQL-brightgreen)
![Frontend tests: 18 passing](https://img.shields.io/badge/frontend_tests-18_passing-brightgreen)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

![TalentFlow AI — an explainable AI hiring pipeline with structured talent data, semantic matching and recruiter-in-the-loop workflows](docs/assets/banner.svg)

---

## Problem

Recruiting teams drown in unstructured text — job descriptions and hundreds of
resumes, none of it queryable, comparable or auditable. "AI hiring" products
that reduce candidates to one opaque score make hiring *less* accountable, not
more: nobody can explain the number, nobody can defend it to a candidate, and
automation bias quietly does the deciding.

## Solution

TalentFlow AI turns JDs and resumes into **validated structured data**, then
matches candidates requirement-by-requirement with **quoted evidence from the
candidate's own resume** and a **published scoring formula**. A recruiter moves
candidates through a real hiring pipeline; the AI assists, the human decides.
It runs out of the box **without any API key** (deterministic mock mode,
labeled as such everywhere) and uses the current OpenAI API with structured
outputs when a key is configured.

## Screenshots

| Dashboard | Match analysis (explainable scoring) |
|---|---|
| ![Dashboard](docs/screenshots/portfolio_01_dashboard.png) | ![Matching](docs/screenshots/portfolio_04_match_analysis.png) |

| Candidate profile | Pipeline board |
|---|---|
| ![Candidate](docs/screenshots/portfolio_03_candidate_profile.png) | ![Pipeline](docs/screenshots/portfolio_05_pipeline.png) |

| Jobs | Screening questions | System health |
|---|---|---|
| ![Jobs](docs/screenshots/portfolio_02_jobs.png) | ![Screening](docs/screenshots/portfolio_06_screening.png) | ![Health](docs/screenshots/portfolio_07_health.png) |

More (including the full acceptance run and the Docker/PostgreSQL verification)
in `docs/screenshots/`.

## Key features

* **Jobs** — create from pasted text or an uploaded JD (PDF/DOCX/TXT);
  requirements extracted into must-have vs preferred with skills, years,
  education, location and domain signals.
* **Candidates** — multi-file resume upload; validated profiles with
  experience timeline, education, certifications, canonicalized skills (each
  with an evidence line) and computed years of experience.
* **Matching** — ranked, requirement-by-requirement: `met / partial / missing /
  unknown`, related-skill partial credit, quoted evidence, component breakdown,
  published weights, deterministic ranking.
* **Pipeline** — NEW → SCREENING → SHORTLISTED → INTERVIEW → OFFER → HIRED
  (+ REJECTED off-ramp) with an append-only audit trail of every move.
* **Notes & tags** — recruiter context with author and timestamps.
* **Screening questions** — per application, grounded in match results
  (strengths, honest gap probes, seniority-calibrated behavioral), each with a
  rationale.
* **System health** — live database + AI configuration checks, counts, no
  secret exposure.

## How AI is used

AI is used in exactly **four** places, each behind a provider interface with a
deterministic offline counterpart:

| Task | Provider | Output validation |
|---|---|---|
| JD → structured job + requirements | OpenAI Responses API, structured outputs | Pydantic schema, then normalization (canonical skills, range checks) |
| Resume → structured candidate profile | same | same |
| Screening-question generation | same | Pydantic schema (categories restricted), stored with rationale |
| Embeddings for semantic similarity | `text-embedding-3-small` (1536-dim) | dimension guard; embedder recorded per vector |

Everything else — requirement evaluation, evidence retrieval, scoring,
ranking, pipeline logic — is deterministic Python. Without `OPENAI_API_KEY`
the platform runs the **mock provider** (rule-based parsers + hashed-ngram
embeddings) and every record is labeled `extraction_method="mock"` in the API,
database and UI. See `docs/AI_DESIGN.md`.

## Explainable matching

No mysterious score. For every candidate↔job pair the engine returns:

* per-requirement status with a **written reason** (`met`, `partial`,
  `missing`, `unknown`, `advisory` for soft requirements);
* **quoted evidence** for met/partial requirements — snippets that literally
  appear in the candidate's resume text (or an explicitly computed statement
  like "7.2 years across 2 dated roles, computed from resume dates");
* **coverage counts** (must-have / preferred: met / partial / missing);
* a **composite score with its published formula** rendered in the UI, e.g.
  `0.60·must_have[75%] + 0.20·preferred[50%] + 0.10·experience[100%] + 0.10·domain[100%] = 75/100 (weights re-normalized over present components)`;
* **semantic similarity** as a supporting signal that can never override a
  deterministic miss.

The engine version is included in every result; the same inputs always produce
the same output. Full specification: `docs/MATCHING.md`; context: `docs/ARCHITECTURE.md §4.3` and `docs/adr/0003`.

## Architecture

```mermaid
flowchart LR
    R[Recruiter browser] --> W[Next.js 16 UI]
    W -- "REST /api/v1 · typed client" --> A[FastAPI services]
    A <--> DB[(PostgreSQL 16 + pgvector)]
    A -- provider interface --> AI["AI layer — OpenAI Responses API<br/>(or deterministic mock)"]
```

A modular monolith: thin versioned API routes → service layer (all business
rules) → SQLAlchemy models on PostgreSQL with pgvector; an AI provider
interface isolates every model call behind a deterministic offline
counterpart. Deep dives: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (with
Mermaid diagrams), [docs/MATCHING.md](docs/MATCHING.md),
[docs/AI_DESIGN.md](docs/AI_DESIGN.md), [docs/API.md](docs/API.md), ADRs in
[docs/adr/](docs/adr/).

## How it works

1. **Create a job** — paste a JD or upload a file (PDF/DOCX/TXT). Extraction
   turns it into structured must-have/preferred requirements (skills, years,
   education, location, domain), schema-validated before persistence, with
   per-record AI provenance.
2. **Upload resumes** — each file becomes a validated candidate profile:
   experience timeline, education, canonicalized skills (each keeping its
   verbatim evidence line), computed years of experience.
3. **Match** — the deterministic engine evaluates every requirement
   (`met`/`partial`/`missing`/`unknown`), quotes the resume evidence, applies
   related-skill partial credit and ranks candidates with a fully published
   formula. Semantic similarity stays a supporting signal — never the verdict.
4. **Work the pipeline** — NEW → SCREENING → SHORTLISTED → INTERVIEW → OFFER
   → HIRED with an append-only audit trail; notes, tags and grounded
   screening questions along the way.
5. **Stay honest** — System Health reports the live database and AI mode;
   mock output is labeled `mock` everywhere and never passed off as a model
   result.

## Responsible AI

No protected characteristics are used, stored or inferred — there is no
column, prompt, or code path for age, gender, ethnicity, religion, disability,
marital status, nationality-as-proxy or photos. A structural test fails the
suite if such a column ever appears; prompts explicitly exclude them; the
platform never issues hire/no-hire verdicts. Read `RESPONSIBLE_AI.md` — it is
a contract, not marketing.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS 4 · self-hosted Inter |
| Backend | Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 · Alembic |
| Database | PostgreSQL 16 + pgvector (HNSW cosine index) · SQLite fallback for dev/tests |
| AI | OpenAI Responses API (structured outputs) + deterministic mock; embeddings 1536-dim |
| Infra | Docker + Docker Compose (any Docker daemon — Desktop, Colima, remote) |
| Quality | pytest (95 tests, 91% coverage) · vitest + Testing Library (18 tests) · ruff · ESLint · strict tsc · GitHub Actions |

## Quick start

### Docker (full stack: PostgreSQL + pgvector)

```bash
git clone <your-fork-url> talentflow-ai && cd talentflow-ai
cp .env.example .env            # optional — every value has a safe default
docker compose up --build -d
docker compose exec api python -m app.seed   # load the synthetic demo dataset
```

Wait for `docker compose ps` to show `db` and `api` as **healthy**, then open:

* **UI:** http://localhost:3000
* **API docs (Swagger):** http://localhost:8000/docs
* **Health:** http://localhost:8000/api/v1/health

### Native (no Docker, SQLite)

```bash
cp .env.example .env
cd backend && uv sync && uv run alembic upgrade head && uv run python -m app.seed && cd ..
cd frontend && npm install && cd ..
make dev        # API :8000 + web :3000 together
```

Requirements: Python 3.12+ (via [uv](https://docs.astral.sh/uv/)), Node 20+.

### Stopping

```bash
docker compose down          # stop the stack (data volumes kept)
make dev                     # native: Ctrl-C stops both processes
```

## Environment variables

All optional — the defaults run the full demo. See `.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | *(unset)* | enables the live OpenAI path (`AI_PROVIDER=auto` picks it up) |
| `AI_PROVIDER` | `auto` | `auto` \| `openai` \| `mock` |
| `OPENAI_MODEL` | `gpt-5.6-terra` | extraction / screening model |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | embeddings (1536-dim) |
| `DATABASE_URL` | *(empty → SQLite)* | PostgreSQL URL (set by compose) |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | allowed browser origins |
| `UPLOAD_DIR` | `./data/uploads` | uploaded file storage |
| `LOG_LEVEL` / `LOG_FORMAT` | `INFO` / text | `LOG_FORMAT=json` for structured logs |
| `WEB_PORT` / `API_PORT` / `POSTGRES_PORT` | `3000` / `8000` / `5432` | compose port mappings |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | where the browser reaches the API |

Secrets are never committed; `.env` is git-ignored; System Health shows only
*whether* a key is configured.

## Demo mode

The default mode is a **deterministic demo**: no API key needed, no network
calls, identical output for identical input. The seed command loads 4 fictional
job postings and 10 fictional candidates whose resumes exist as real
PDF/DOCX/TXT files (`examples/resumes/`) and are ingested through the same
pipeline a live upload uses. `python -m app.seed --reset` wipes and rebuilds.

**Mock vs live is never ambiguous:** every extracted record carries
`extraction_method` (`mock` / `openai`), the UI badges it, and System Health
states the active mode explicitly.

## Testing

```bash
make test                                  # everything below, one command

cd backend && uv run pytest                # 94 passed + 1 skipped (SQLite run)
cd backend && uv run ruff check app tests  # lint
# with the Docker database running — nothing skips:
cd backend && DATABASE_URL="postgresql+psycopg://talentflow:talentflow@localhost:5432/talentflow" \
  uv run pytest                            # 95 passed

cd frontend && npm test && npm run typecheck   # 18 passed + strict TS
```

Coverage: 91% backend. CI runs the same suites (against a real
PostgreSQL+pgvector service container) plus Docker image builds — see
`.github/workflows/ci.yml` and `docs/TESTING.md` for the acceptance checklist and
the E2E scenario.

## Project structure

```text
talentflow-ai/
├── backend/            FastAPI app
│   ├── app/
│   │   ├── ai/         provider interfaces + OpenAI & deterministic mock
│   │   ├── api/        routes, deps, serializers, middleware
│   │   ├── core/       config, logging, errors, dates
│   │   ├── db/         engine/session, declarative base
│   │   ├── models/     SQLAlchemy models (incl. dialect-aware vector column)
│   │   ├── schemas/    Pydantic request/response models
│   │   ├── services/   jobs, candidates, pipeline, screening, matching,
│   │   │               normalization, documents, embeddings_store, skills
│   │   └── seed/       synthetic dataset + `python -m app.seed`
│   ├── alembic/        migrations (PostgreSQL + SQLite)
│   └── tests/          95 tests
├── frontend/           Next.js app (9 pages + typed client + UI kit)
├── .github/            CI + CodeQL workflows, Dependabot, issue/PR templates
├── docs/               architecture, AI design, matching engine, API, testing,
│                       ADRs, maintainer guides, screenshots, banner assets
├── examples/           synthetic JDs + resume files (PDF/DOCX/TXT)
└── scripts/            dev launcher
```

Community files at the root: `LICENSE` (MIT), `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, `ROADMAP.md`,
`RESPONSIBLE_AI.md`.

## API overview

`http://localhost:8000/docs` is the interactive reference; the full table is
in `docs/API.md`. Shape of it:

| Group | Endpoints |
|---|---|
| System | `GET /api/v1/health/live`, `GET /api/v1/health` |
| Jobs | `GET/POST /jobs`, `POST /jobs/upload`, `GET/PATCH/DELETE /jobs/{id}` |
| Candidates | `GET /candidates`, `POST /candidates/upload`, `GET/DELETE /candidates/{id}`, notes & tags sub-resources |
| Pipeline | `GET/POST /applications`, `GET /applications/board`, `GET /applications/activity`, `PATCH /applications/{id}/stage` |
| Matching | `GET /matching/job/{id}`, `GET /matching/candidate/{id}`, `GET /matching/pair` |
| Screening | `GET /screening`, `GET/POST /screening/applications/{id}[/generate]` |

All errors share one shape: `{"error": {"code", "message", "detail?"}}`.

## Roadmap

Current / Next / Future — with explicit non-goals — in
[ROADMAP.md](ROADMAP.md). Highlights: authentication + multi-tenant
workspaces, pagination for large collections, an OpenAI reranking evaluation
harness, CSV export, interview scorecards.

## Known limitations

* **No authentication** — do not expose the demo to the public internet as-is.
* The **mock extractor** is a curated lexicon + rules engine: precision over
  recall, English-centric. It powers the keyless demo, never claims to be a
  model, and is labeled per record.
* **Years of experience** are computed from resume dates (merged ranges), not
  a life history.
* Scanned/image PDFs are rejected (no OCR); upload a text-based file.
* pgvector similarity in mock mode approximates lexical overlap (hashed
  n-grams), not learned semantics.
* Single-process deployment profile (uvicorn workers, no queue) — appropriate
  for demo scale; documented in `SECURITY.md` and `docs/ARCHITECTURE.md`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — synthetic data only, explainability
guarantees are a contract, and `main` stays green. Community expectations:
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security issues:
[SECURITY.md](SECURITY.md) (private reporting only). Release history:
[CHANGELOG.md](CHANGELOG.md). New to GitHub or to maintaining a project? Start
with [docs/GITHUB_FOR_OWNER.md](docs/GITHUB_FOR_OWNER.md) and
[docs/MAINTAINER_GUIDE.md](docs/MAINTAINER_GUIDE.md).

## Development transparency

Parts of this repository were developed with AI coding assistants working
from human-authored specifications, architecture decisions and review. The
project owner maintains the repository and owns every change; every behavior
claim in this README is backed by the test suite, the CI pipeline, or an
executed acceptance run (recorded in
[CHATGPT_REVIEW_HANDOFF.md](CHATGPT_REVIEW_HANDOFF.md)). The commit history is
real work, not manufactured activity.

## License

MIT — see `LICENSE`.
