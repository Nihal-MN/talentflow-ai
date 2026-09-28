# ChatGPT Review Handoff — TalentFlow AI

Engineering handoff for an independent review of this repository. Written by
the implementing agent after a full production-style audit (28 Sep 2026).
No marketing: everything below is checkable against the repo.

**Reviewed code state:** commit `e6e0005` (`chore: production audit …`).
**How to verify anything here:** every claim names the file or command that
proves it.

---

## 1. Repository structure

```text
talentflow-ai/
├── backend/                  Python 3.12 / FastAPI service
│   ├── app/
│   │   ├── main.py           app factory (routers, CORS, middleware, handlers)
│   │   ├── core/             config.py, logging.py, errors.py, dates.py
│   │   ├── db/               base.py (declarative base), session.py (engine)
│   │   ├── models/           candidate.py, job.py, application.py, note.py,
│   │   │                     tag.py, screening.py, embedding.py
│   │   ├── schemas/          Pydantic request/response models
│   │   ├── ai/               base.py, openai_provider.py, mock_provider.py,
│   │   │                     mock_jd.py, mock_resume.py, embeddings.py,
│   │   │                     factory.py, prompts.py, schemas.py, cities.py
│   │   ├── services/         documents.py, normalization.py, skills.py,
│   │   │                     embeddings_store.py, matching.py,
│   │   │                     matching_evidence.py, job_service.py,
│   │   │                     candidate_service.py, pipeline.py, screening.py
│   │   ├── api/              deps.py, middleware.py, serializers.py,
│   │   │                     routes/{health,jobs,candidates,applications,
│   │   │                     matching,screening,tags}.py
│   │   └── seed/             demo_jobs.py, demo_candidates*.py,
│   │                         generate_files.py, run_seed.py
│   ├── alembic/versions/     3dc9b96a8fcf_initial_schema.py (single migration)
│   ├── tests/                12 test modules, 95 tests
│   ├── scripts/smoke_api.py  human-readable end-to-end script
│   ├── pyproject.toml + uv.lock, Dockerfile, docker-entrypoint.sh
├── frontend/                 Next.js 16 (App Router) / React 19 / TS
│   ├── src/app/              page.tsx (dashboard), jobs/, jobs/new,
│   │                         jobs/[id], candidates/, candidates/[id],
│   │                         matching/, pipeline/, screening/, health/
│   ├── src/components/       shell/, ui/, jobs/, candidates/, matching/,
│   │                         pipeline/
│   ├── src/hooks/useApi.ts   fetch hook (request-id guarded)
│   ├── src/lib/              api.ts (typed client), types.ts, format.ts
│   └── src/**/*.test.ts(x)   3 test files, 18 tests
├── docs/                     adr/0001-0004, screenshots/ (24 files)
├── examples/                 jobs/ (4 JDs), resumes/ (10 files: PDF/DOCX/TXT)
├── scripts/dev.sh            native dev launcher
├── .github/workflows/ci.yml  backend / frontend / docker jobs
├── docker-compose.yml        db (pgvector) + api + web
└── Makefile                  setup/up/down/seed/test/lint/health/dev
```

## 2. Architecture

Modular monolith (ADR 0001). Layers, strictly:

```text
browser → Next.js pages (client components, typed client)
        → FastAPI routers (/api/v1, thin) → app/api/serializers.py
        → domain services (fields of app/services — the ONLY mutation path)
        → SQLAlchemy models → PostgreSQL (or SQLite)
AI is reachable only through app/ai/base.py protocols; the matching engine
(app/services/matching.py) reads stored data and never calls an LLM.
```

Key invariants (enforced in review + tests):
- routers never touch models directly;
- no LLM SDK import outside `app/ai/`;
- raw model output is never persisted without Pydantic + normalization;
- documents are treated as untrusted data end-to-end.

## 3. Technology stack (as actually used)

- Python 3.12, FastAPI 0.141, Pydantic 2.13 (+pydantic-settings), SQLAlchemy 2.1,
  Alembic, psycopg 3, pgvector-python, NumPy, pypdf, python-docx, fpdf2
  (seed-time PDF generation only), OpenAI SDK 2.x.
- Next.js 16.3 (App Router, Turbopack build), React 19.3, TypeScript 5.9,
  Tailwind CSS 4.3, @fontsource-variable/inter (self-hosted).
- PostgreSQL 16 + pgvector via `pgvector/pgvector:pg16`; SQLite fallback.
- pytest 9 (+pytest-cov), vitest 5 + Testing Library, ruff, ESLint 9
  (eslint-config-next flat config), GitHub Actions.

## 4. Important files (review starting points)

| File | Why it matters |
|---|---|
| `backend/app/services/matching.py` | the explainable matching engine (statuses, weights, composite, evidence assembly) |
| `backend/app/models/embedding.py` | dialect-aware vector column (`EmbeddingVector` TypeDecorator) |
| `backend/app/services/embeddings_store.py` | chunking, storage, similarity search (pgvector `<=>` vs in-process cosine) |
| `backend/app/ai/base.py` | provider protocols + dataclasses — the AI seam |
| `backend/app/ai/openai_provider.py` | exact OpenAI integration (Responses API + `text_format`) |
| `backend/app/services/normalization.py` | the validation gate before persistence |
| `backend/app/api/serializers.py` | ORM→API mapping incl. computed fields |
| `frontend/src/lib/api.ts` | the full API surface the UI consumes |
| `frontend/src/components/matching/MatchCard.tsx` | how explainability is rendered |
| `backend/tests/test_matching_engine.py` | behavioral guarantees incl. the protected-columns guard |

## 5. Database schema (14 tables)

```text
candidates(id, full_name, email, phone, location, headline, summary,
           years_experience, linkedin_url, github_url, website_url,
           resume_filename, resume_path, resume_text, extraction_method,
           extraction_model, created_at, updated_at)
candidate_experiences / candidate_educations / candidate_skills / candidate_certifications
    (children of candidate; skills have UNIQUE(candidate_id, normalized_name))
jobs(id, title, company, location, employment_type, seniority, domain, status,
     description_text, source, extraction_method, extraction_model, …)
job_requirements(id, job_id, kind must_have|preferred, category
     skill|experience|education|certification|domain|location|other, label,
     normalized_skill, min_years, keywords, order_index)
applications(id, candidate_id, job_id, stage, UNIQUE(candidate_id, job_id))
     stage ∈ NEW, SCREENING, SHORTLISTED, INTERVIEW, OFFER, HIRED, REJECTED (strings)
pipeline_stage_events(id, application_id, from_stage, to_stage, note)  -- audit trail
candidate_notes(id, candidate_id, job_id?, author, body)
tags + candidate_tags (M2M)
screening_questions(id, application_id, category, question, rationale, source)
embedding_records(id, owner_type candidate|job, owner_id, chunk_index,
     chunk_text, embedder, embedding vector(1536) on PG / TEXT on SQLite,
     UNIQUE(owner_type, owner_id, chunk_index))
```

Migration: `backend/alembic/versions/3dc9b96a8fcf_initial_schema.py` —
creates all tables on both dialects, `CREATE EXTENSION vector` + HNSW index
(`vector_cosine_ops`) on PostgreSQL only, reversible (`downgrade` verified).
Verify: `cd backend && uv run alembic upgrade head && uv run alembic check`.

## 6. API endpoints (24 paths, OpenAPI at /openapi.json)

```text
GET  /api/v1/health/live            liveness
GET  /api/v1/health                 db status/latency/dialect, AI config, counts
GET  /api/v1/jobs                   list (must/preferred/app counts)
POST /api/v1/jobs                   create from pasted JD {title?, company?, jd_text}
POST /api/v1/jobs/upload            multipart file (PDF/DOCX/TXT)
GET|PATCH|DELETE /api/v1/jobs/{id}  detail / status update / delete
GET  /api/v1/candidates             list (q, skill filters)
POST /api/v1/candidates/upload      multipart resume → structured profile (201)
GET|DELETE /api/v1/candidates/{id}
POST /api/v1/candidates/{id}/notes  | DELETE …/notes/{note_id}
POST /api/v1/candidates/{id}/tags   | DELETE …/tags/{tag_id}
GET  /api/v1/applications           list (?job_id, ?candidate_id, ?stage)
POST /api/v1/applications           add to pipeline (idempotent per pair)
GET  /api/v1/applications/board     { NEW: [...], SCREENING: [...], … }
GET  /api/v1/applications/activity  recent stage changes (dashboard feed)
GET  /api/v1/applications/{id}      detail incl. stage_events audit trail
PATCH /api/v1/applications/{id}/stage   {to_stage, note?} (same-stage = no-op)
GET  /api/v1/matching/job/{job_id}      ranked candidates (the core endpoint)
GET  /api/v1/matching/candidate/{id}    ranked jobs
GET  /api/v1/matching/pair              ?job_id&candidate_id explainer
GET  /api/v1/screening                  applications with stored question sets
GET|POST /api/v1/screening/applications/{id}[/generate]
GET  /api/v1/tags                       tags + usage counts
```

Errors: uniform `{"error": {"code", "message", "detail?"}}` via
`app/core/errors.py` (`not_found`, `validation_error`, `ingestion_error`,
`conflict`, `provider_unavailable`, `http_error`). Every path above is
exercised by tests or the E2E run.

## 7. AI functionality (complete list)

1. **JD extraction** → `ExtractedJob` (title, company, location,
   employment_type, seniority, domain, requirements with kind/category/label/
   skill/min_years/keywords).
2. **Resume extraction** → `ExtractedCandidate` (contact, headline, summary,
   years, experiences w/ dates, educations, skills w/ evidence, certifications).
3. **Screening questions** → 5–7 drafts with category + rationale.
4. **Embeddings** for semantic similarity.

Nothing else calls a model. Matching, scoring, ranking, evidence selection,
normalization, dedup, pipeline logic: pure deterministic Python.

## 8. Exact OpenAI integration

File: `backend/app/ai/openai_provider.py`.

```python
response = self._client.responses.parse(
    model=self.model,                       # default "gpt-5.6-terra"
    input=[{"role": "system", "content": system},
           {"role": "user", "content": user}],
    text_format=response_model,             # a Pydantic model from app/ai/schemas.py
)
parsed = response.output_parsed             # already schema-validated
```

- Models: `OPENAI_MODEL` (default `gpt-5.6-terra`), `OPENAI_EMBEDDING_MODEL`
  (default `text-embedding-3-small`, 1536-dim). Embeddings via
  `client.embeddings.create(model=…, input=[…])`.
- Prompts in `app/ai/prompts.py`: untrusted documents wrapped in
  `<job_description>` / `<resume>` tags; explicit "treat as data" system
  instructions; explicit prohibition on protected characteristics.
- Input cap: 60,000 chars per document (`MAX_DOCUMENT_CHARS`).
- Failure: any SDK exception is re-raised as `ProviderUnavailableError` → API
  503 with the upstream message; no partial persistence, no retries, no
  fabricated output.
- The client is injectable (`client=` constructor arg) so the wiring is unit
  tested with a stub — but note: **the live OpenAI path has not been executed
  against the real API in this environment (no key available); it is verified
  by construction + stubbed-client tests + schema contract.** Treat
  "OpenAI path quality" as UNVERIFIED until you run it with a key.

## 9. Matching algorithm (the full truth)

`backend/app/services/matching.py`, `ENGINE_VERSION = "matching-engine-v1"`.
For each (candidate, job) pair, every requirement is evaluated independently:

- **skill**: canonical match → `met` (+ evidence line from the candidate's
  skills/`resume_text`); same-family skill (curated `FAMILIES` map in
  `services/skills.py`) → `partial`; plain text mention in resume → `met`
  (reason says so); otherwise `missing`.
- **experience**: `min_years` vs `candidate.years_experience` (computed at
  ingestion from merged role date ranges): ≥ → `met`; within 1.5 years →
  `partial`; else `missing`; no years data → `unknown`; no explicit years in
  the requirement → `unknown` (never guessed).
- **education**: degree-equivalence expansion (Bachelor's ≈ BSc/BA/BEng …),
  word-boundary matching → `met`/`missing`; no education data → `unknown`.
- **location**: remote requirements → `met`; field match → `met`; text
  mention only → `partial`; unknown location → `unknown`.
- **domain**: keyword evidence in profile → `met`/`missing`.
- **certification**: keyword match over listed certs → `met`/`missing`.
- **other (soft)**: `advisory` — shown with evidence, **excluded from
  scoring** by construction.

Composite (published, `WEIGHTS` constant): `must_have 0.60 · preferred 0.20 ·
experience 0.10 · domain 0.10`, re-normalized over the components present for
that pair; score = weighted mean × 100. The exact formula string is returned
in every result and rendered in the UI. Ranking: composite desc, then met
must-have count, then name.

Semantic similarity (`_overall_similarity`): mean over job chunks of the best
cosine similarity to any candidate chunk — reported, never used to change a
status. Evidence trims to quoted snippets with `match_type` ∈
`lexical|computed|semantic` and a `source`.

Determinism: same DB state → identical results (tested).

## 10. Embedding implementation

- `app/ai/embeddings.py`: `HashEmbeddingProvider` (mock) hashes token
  unigrams+bigrams via blake2b into 1536 dims with ±1 signs, L2-normalized —
  deterministic offline; `OpenAIEmbeddingProvider` for live mode. `cosine_similarity()`
  helper (numpy, defensive against empty/mismatched vectors).
- Chunking (`embeddings_store.build_candidate_chunks/build_job_chunks`):
  candidate → header/summary/roles/skills/education lines; job → overview +
  one chunk per requirement. Chunk text is stored so semantic hits are
  traceable. Caps: 24 chunks/owner, 1500 chars/chunk.
- Storage lifecycle: delete-then-insert per owner (idempotent; bulk DELETE to
  avoid unique-constraint races), dimension guard (raises a typed error on
  mismatch), embedder recorded per row (`mock:hashed-ngram-v1` /
  `openai:text-embedding-3-small`).

## 11. pgvector usage

- Column: `embedding vector(1536)` (PostgreSQL) / JSON TEXT (SQLite) —
  `app/models/embedding.py::EmbeddingVector` TypeDecorator. On PG, binds pass
  raw lists through (pgvector's type formats them); results parse from
  ndarray/list/text.
- Search (`search_similar`): PG branch executes
  `ORDER BY embedding <=> CAST(:query_vector AS VECTOR(1536)) LIMIT k` with
  `type_coerce(..., Float)` on the distance expression (so the distance — not
  the vector column type — governs result processing). SQLite branch computes
  cosine in-process over the owner's rows.
- Index: HNSW `vector_cosine_ops`, created in the migration, verified present
  in the live database (`SELECT indexname FROM pg_indexes …` shows
  `ix_embedding_records_embedding_hnsw`).
- Verified end-to-end: `tests/test_postgres_path.py` (stored two vectors
  against the real server, ranked search returned the semantically closer
  chunk first, round-trip dims == 1536). Bug found and fixed during the
  audit: PG insert binding + distance typing (commit `b6143b3`).

## 12. Resume ingestion flow (exact)

```text
POST /candidates/upload (multipart ≤10MB)
→ app/services/documents.extract_text   (extension allow-list; pypdf/docx/plain
   decode with BOM detection; sanitize; ≥30 meaningful chars)
→ app/services/documents.save_upload    (uuid-prefixed storage under UPLOAD_DIR)
→ provider.extract_candidate(...)       (OpenAI or mock; 60k char cap)
→ app/services/normalization.normalize_candidate
   (strings cleaned, skills canonicalized+deduped, year ranges clamped/dropped,
    dates sanity-checked, evidence preserved)
→ app/services/candidate_service.ingest_resume
   (single transaction: Candidate + experiences/educations/skills/certs +
    embeddings; extraction_method/model recorded)
→ 201 with the validated profile (app/api/serializers.candidate_out)
```

## 13. JD ingestion flow (exact)

```text
POST /jobs            (JSON: jd_text ≥30 chars)  ─┐
POST /jobs/upload     (multipart file)            ─┴→ same path after extraction
→ provider.extract_job(...)  → normalize_job (kinds/categories validated,
   requirements deduped, keywords capped)
→ job_service.create_job: Job + JobRequirement rows + job embeddings, commit
→ 201 JobOut (requirements with kind/category/skill/min_years/keywords)
```

## 14. Pipeline implementation

- `applications.stage` is a plain string from the enum `PipelineStage`
  (NEW/SCREENING/SHORTLISTED/INTERVIEW/OFFER/HIRED/REJECTED); validated in
  `services/pipeline.py`.
- `create_application` is idempotent per (candidate, job) and records an
  initial `PipelineStageEvent(None → stage)`.
- `move_stage` validates the target, writes an event row with optional note,
  returns the application; same-stage moves are no-ops (no duplicate events).
- `get_board` returns all seven stages (empty lists included); `recent_activity`
  powers the dashboard feed.
- UI: pipeline board columns + `StageControls` (explicit select / advance /
  reject — accessible and testable; no drag-only interaction).

## 15. Testing architecture

- **Hermetic first**: `backend/tests/conftest.py` sets `DATABASE_URL=sqlite://`
  + `AI_PROVIDER=mock` + empty key, builds a shared in-memory DB with FK
  pragmas on, overrides `get_db` and both provider dependencies, and wipes all
  tables between tests. No network, no keys, no shared state.
- **Comprehensive**: 12 modules / 95 tests — health, jobs (extraction quality
  assertions), candidates (PDF/DOCX/TXT ingestion, notes, tags, error paths),
  documents (encodings, corrupt PDFs, caps), mock extraction (section
  detection, boundary precision, determinism), normalization, skill taxonomy,
  matching engine (every status path + guarantees + regression tests),
  matching API, pipeline (audit trail, no-op moves, board), screening,
  embeddings + migration round-trip, PostgreSQL/pgvector path.
- **PostgreSQL integration**: `tests/test_postgres_path.py` — two
  dialect-level checks always run; the full pgvector round-trip runs whenever
  `DATABASE_URL` points at PostgreSQL (locally against the Docker db, in CI
  against a service container).
- **Frontend**: vitest + Testing Library — formatting/constants, API client
  error shaping (structured errors, network failure, 204, FormData vs JSON),
  MatchCard rendering (score, formula, expandable evidence, pipeline
  affordance), StageControls behavior, badges.
- **End-to-end**: documented manual acceptance checklist (TESTING.md) executed
  against the live Docker stack with browser automation; screenshots committed.
- **Structural guards**: no protected-attribute columns may exist
  (`test_no_protected_attribute_columns_exist_anywhere`); migrations must
  round-trip; embeddings dimension must match storage.

## 16. Security controls

See SECURITY.md §7 for the audit table. Summary: no secrets in git history or
code; `.env` untracked; uploads validated (type allow-list, 10 MB cap,
parser isolation, escaped rendering); SQLAlchemy parameter binding everywhere;
PII-free logs; CORS allow-list; uniform structured errors; dependency
lockfiles frozen in CI. **No authentication** — documented as pre-deployment
work; the service layer is the single mutation choke-point where auth can be
added.

## 17. Responsible AI controls

See RESPONSIBLE_AI.md. Mechanically enforced: protected attributes have no
schema columns (tested), prompts exclude them, screening categories are
restricted (`technical/gap_probe/experience/behavioral`, tested), matching
never infers them, and no endpoint emits a hire/no-hire verdict. Every
automated judgement is traceable to quoted evidence + published weights.

## 18. Environment variables

| Variable | Default | Notes |
|---|---|---|
| `OPENAI_API_KEY` | unset | enables live mode via `AI_PROVIDER=auto` |
| `AI_PROVIDER` | `auto` | `auto`/`openai`/`mock` |
| `OPENAI_MODEL` | `gpt-5.6-terra` | overridable |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | 1536-dim |
| `DATABASE_URL` | empty → SQLite file | compose injects PostgreSQL URL |
| `CORS_ORIGINS` | localhost:3000 list | allow-list |
| `UPLOAD_DIR` | `./data/uploads` | file storage |
| `LOG_LEVEL` / `LOG_FORMAT` | `INFO` / text | `json` for structured logs |
| `WEB_PORT` / `API_PORT` / `POSTGRES_PORT` | 3000 / 8000 / 5432 | compose |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | baked into the web build |

## 19. Startup instructions

```bash
git clone <repo-url> talentflow-ai && cd talentflow-ai
cp .env.example .env
docker compose up --build -d          # db → api → web (healthchecks gate order)
docker compose exec api python -m app.seed
# UI: http://localhost:3000 · API docs: http://localhost:8000/docs
# Health: http://localhost:8000/api/v1/health
```
Native alternative: `make setup && make seed-native && make dev`
(see README). Clean-start (volumes wiped → rebuild → healthy) was verified:
`docker compose down -v && docker compose up --build -d`.

## 20. Test commands

```bash
make test                                            # backend + frontend
cd backend && uv run pytest                          # 94 passed, 1 skipped (SQLite)
cd backend && DATABASE_URL="postgresql+psycopg://talentflow:talentflow@localhost:5432/talentflow" \
  uv run pytest                                       # 95 passed, 0 skipped
cd backend && uv run ruff check app tests
cd frontend && npm test && npm run typecheck && npm run lint && npm run build
cd backend && uv run python scripts/smoke_api.py     # end-to-end in-process script
```

## 21. Demo instructions

Default mock mode needs no key. `python -m app.seed` (or `--reset`) loads 4
fictional jobs + 10 candidates whose PDF/DOCX/TXT files (`examples/resumes/`)
are ingested through the real pipeline. For a live-mode demo: set
`OPENAI_API_KEY` in `.env`, restart the api container
(`docker compose up -d api`), re-run the seed; records produced by OpenAI are
labeled `extraction_method="openai"` and badged in the UI.

## 22. Known limitations

* No authentication / multi-tenancy (pre-deployment work).
* OpenAI path UNVERIFIED against the live API in this environment (no key);
  covered by stubbed-client tests + schema contracts only.
* Mock extractor: curated lexicon (English-centric, precision-over-recall);
  clearly labeled, never presented as model output.
* Years of experience computed from resume dates (merged ranges).
* Scanned/image PDFs rejected (no OCR).
* Mock embeddings approximate lexical similarity (hashed n-grams).
* Composite weights are a documented heuristic, not a science.
* Single-worker deployment profile; no queue/async — demo scale.

## 23. Outstanding TODOs

None in code (greps for TODO/FIXME/HACK/placeholder across app, tests, docs and
CI return nothing). The items under "Roadmap" in README.md are **planned
scope**, deliberately not stubs. If you want a TODO list for a v2, start with
auth, then CSV export, then reranking evaluation.

## 24. Current Git commit hash

- Code state reviewed: `e6e000535bb526ce1299ec339d3aa3825d4b9d95` (`e6e0005`).
- This document + the two companion docs are committed immediately after it;
  run `git log --oneline -3` for the exact tip.

## 25. Test results (actual, 28 Sep 2026)

```text
Backend (SQLite, hermetic):   94 passed, 1 skipped in 1.65s
Backend (PostgreSQL+pgvector): 95 passed in 1.67s   ← Docker db running
Coverage:                      91% (2851 stmts, 253 missed)
Frontend:                      18 passed (3 files)
Lint:                          ruff clean; eslint clean; tsc --noEmit clean
Smoke script:                  SMOKE TEST PASSED (job → resume → match →
                               stages → note → screening, in-process)
E2E (live Docker stack, browser-automated): all 19 scenario steps passed —
job with Node.js/React/TypeScript/Microservices/AWS/Kafka requirements
extracted; 3 resumes (PDF/DOCX/TXT) ingested; ranked matching with
matched/missing requirements and quoted evidence; candidate detail;
screening questions generated; NEW→SCREENING→SHORTLISTED with audit trail;
recruiter note; persistence verified after hard refresh (and across an api
container recreation during the audit); System Health all-operational.
```

## 26. Build results (actual)

```text
frontend build (clean npm ci, 461 packages): ✓ compiled, 10 routes generated
backend image: ✓ built (python:3.12-slim + uv frozen lockfile)
web image:     ✓ built (node:22-alpine, standalone output)
docker compose up --build (clean start, volumes wiped): db healthy → api
healthy (migrations ran: alembic upgrade head, incl. CREATE EXTENSION vector
+ HNSW index) → web started; health endpoint reports dialect=postgresql.
```

## 27. Functionality that remains mocked (explicit list)

Only these, all labeled in-product and in the API:

1. **LLM extraction + screening questions** run the deterministic mock provider
   when no key is set (`extraction_method="mock"`, UI badge "mock AI").
2. **Embeddings** are the hashed-ngram mock (`embedder="mock:hashed-ngram-v1"`)
   in default mode.
3. **Similarity search on SQLite** is computed in-process (dev/test fallback);
   the pgvector SQL path is what runs on PostgreSQL.
4. **Demo data** is synthetic (by design — no real PII anywhere).

Nothing else is mocked: pipeline, notes/tags, health, matching, evidence,
ranking, migrations and the UI flows are the real implementations exercised by
the tests and the E2E run above.

