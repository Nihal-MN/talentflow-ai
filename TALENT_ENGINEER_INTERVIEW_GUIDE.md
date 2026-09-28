# Talent Engineer Interview Guide — TalentFlow AI

You built this. This guide teaches you to *defend* it. For every technology
actually used in the repository: what it is, why TalentFlow uses it, where the
code lives, what breaks if you remove it, and how to talk about it in an
interview. Nothing here is aspirational — every claim matches the code you can
open right now.

**How to use this:** read it once end-to-end, then open the repository and
trace three flows in the actual code (job creation, resume upload, matching).
If you can narrate those three flows with the file names below, you can pass
the interview.

---

## 1. FastAPI

- **What it is:** a modern Python web framework for building REST APIs; you
  declare endpoints as functions with type-annotated parameters, and FastAPI
  generates validation, error responses and interactive docs (`/docs`).
- **Why TalentFlow uses it:** the product is fundamentally a CRUD + compute
  API for jobs, candidates, applications and matching. FastAPI gives typed
  request/response contracts, dependency injection (for the DB session and AI
  providers) and free OpenAPI documentation — all of which a recruiter-facing
  demo and a reviewer lean on.
- **Where:** `backend/app/main.py` (app factory), `backend/app/api/routes/*`
  (the 7 routers), `backend/app/api/deps.py` (dependency injection).
- **Without it:** you'd hand-write an HTTP layer in Flask/Django; you'd lose
  automatic validation, the OpenAPI schema (and therefore the typed frontend
  client), and dependency overrides (which is how the tests inject a mock
  database).
- **Interview line:** "The API is versioned under `/api/v1`, routers are thin
  and only translate HTTP to service calls and back; all business rules live
  in the service layer, which is what makes it testable."

## 2. REST API design

- **What it is:** resource-oriented HTTP: nouns as URLs, verbs as methods
  (`GET /jobs/5`, `POST /jobs`, `PATCH /applications/3/stage`), status codes
  as outcomes (201 created, 404 missing, 422 invalid).
- **Why TalentFlow uses it:** the frontend and any future integration (ATS,
  CLI) speak one stable contract. Every error has one JSON shape:
  `{"error": {"code", "message", "detail?"}}`, so the UI renders failures
  without string-matching.
- **Where:** `backend/app/api/routes/` and the error taxonomy in
  `backend/app/core/errors.py`; the frontend mirror is `frontend/src/lib/api.ts`.
- **Without it:** ad-hoc endpoints and inconsistent errors → the typed client
  and the tests that assert error shapes would collapse.
- **Interview line:** "Errors are a product surface. Same shape everywhere,
  machine-readable codes — the frontend has one `ApiError` class and one
  `ErrorState` component for every failure in the app."

## 3. PostgreSQL

- **What it is:** the production-grade relational database. Reliable
  transactions, foreign keys, indexes, concurrent access.
- **Why TalentFlow uses it:** recruiting data is deeply relational
  (candidates → experiences/skills; applications → jobs; stage events as an
  audit trail). FKs with `ON DELETE CASCADE` keep integrity; the same
  database hosts the `pgvector` extension for embeddings, so operational data
  and semantic search live in one store.
- **Where:** `docker-compose.yml` (`pgvector/pgvector:pg16`), models in
  `backend/app/models/`, migrations in `backend/alembic/`.
- **Without it:** SQLite would technically keep the demo running (it's the
  dev/test fallback), but you'd lose real concurrency, the vector index, and
  the production story.
- **Interview line:** "One Postgres serves both the relational domain and the
  vector search via the pgvector extension — one store to operate, one
  backup story, joins stay possible."

## 4. SQLAlchemy

- **What it is:** Python's main ORM — you define classes (models) that map to
  tables, and query them with type-safe expressions instead of string SQL.
- **Why TalentFlow uses it:** the domain model is rich (14 tables); the ORM
  gives relationships, cascades, and dialect portability (the same model code
  runs on PostgreSQL and SQLite). Session-per-request keeps transactions
  explicit, and everything is parameterised (no SQL injection).
- **Where:** `backend/app/db/` (base + session), `backend/app/models/*`,
  queries in `backend/app/services/*`.
- **Without it:** hand-written SQL for 14 tables × two dialects, or a lighter
  query builder with less modelling leverage.
- **Interview line:** "Services own the session and commit once per operation —
  a resume upload is a single transaction: candidate, children rows and
  embeddings either all land or none do."

## 5. Pydantic

- **What it is:** Python validation layer — declare shapes with types, and
  input/output is validated and coerced at the boundary.
- **Why TalentFlow uses it twice:** (1) API schemas (`backend/app/schemas/`)
  validate every request/response; (2) — the interesting part — the **same
  idea gates LLM output**: `backend/app/ai/schemas.py` defines the exact
  structured output contract, and a model response that doesn't fit is
  rejected before it can touch the database.
- **Where:** schemas/, ai/schemas.py, and the normalization gate in
  `backend/app/services/normalization.py`.
- **Without it:** raw LLM JSON and raw request payloads would flow straight
  into the database — the project's core honesty claim ("no unvalidated model
  output becomes truth") would be false.
- **Interview line:** "Validation is the boundary between 'text that looks
  like data' and 'data I'm willing to store'. The LLM is untrusted input, same
  as a resume file."

## 6. Docker

- **What it is:** containerisation — the app, its OS-level dependencies and
  its runtime are packaged into an image that runs identically anywhere.
- **Why TalentFlow uses it:** the target experience is `git clone → cp
  .env.example .env → docker compose up --build` and everything works — no
  Python/Node/Postgres installation required. It also makes CI reproducible.
- **Where:** `backend/Dockerfile` (+ `docker-entrypoint.sh` which runs
  migrations then starts uvicorn), `frontend/Dockerfile` (multi-stage,
  Next.js standalone output), `docker-compose.yml` (three services with
  healthcheck-gated startup).
- **Without it:** every reviewer would need a working local Postgres,
  matching Python 3.12, Node 22 — the demo's friction would go way up.
- **Interview line:** "Compose starts in dependency order via healthchecks:
  the API waits for a *healthy* database, runs Alembic, then serves — so a
  fresh clone can't race its own migrations."

## 7. Next.js

- **What it is:** the React framework — routing (App Router), server/client
  component split, build tooling and production server for the UI.
- **Why TalentFlow uses it:** nine product pages with shared navigation and
  typed API access. The App Router gives file-based routes
  (`app/jobs/[id]/page.tsx`), and the standalone production build ships as a
  slim Docker image.
- **Where:** `frontend/src/app/**` (pages, layout, global styles);
  `frontend/next.config.mjs` sets `output: "standalone"`.
- **Without it:** a bare React + bundler setup you'd have to assemble
  yourself (routing, build, server).
- **Interview line:** "Pages are client components — this is a live-data app,
  every page fetches through one typed client (`src/lib/api.ts`), and each
  page implements loading, empty, error and success states."

## 8. React

- **What it is:** the component model for the UI — state in components,
  re-render on change, composition over inheritance.
- **Why TalentFlow uses it:** the matching view is genuinely interactive
  (expandable evidence rows, regenerate questions, move stages, add tags) and
  must reflect server state immediately after actions.
- **Where:** `frontend/src/components/**` (UI kit, MatchCard, StageControls,
  panels) and the pages under `frontend/src/app/`.
- **Without it:** server-rendered templates with full page reloads; the
  evidence-explorer interaction that *is* the product's differentiator would
  be clunky.
- **Interview line:** "The one custom hook is `useApi` — it guards against
  out-of-order responses with a request id and distinguishes a visible
  reload from a silent background refetch."

## 9. TypeScript

- **What it is:** JavaScript plus a static type system, checked at build time.
- **Why TalentFlow uses it:** the API contract is the source of truth; the
  frontend mirrors it by hand in `frontend/src/lib/types.ts` and the typed
  client refuses calls that don't match. Refactoring UI code without a type
  checker on a 4k-line codebase is how you ship `undefined` to a screen.
- **Where:** everything under `frontend/src/`; enforced by `tsc --noEmit` in
  `make test-frontend` and CI.
- **Without it:** the classic class of bugs: renamed fields, missing null
  checks (`years_experience: number | null` everywhere for a reason).
- **Interview line:** "The Pydantic schemas on the backend and `types.ts` on
  the frontend are deliberately hand-kept twins — no codegen step to maintain,
  and the compiler catches drift in either direction the moment a shape
  changes."

## 10. LLMs

- **What it is:** large language models — probabilistic text transformers,
  accessed via an API; excellent at parsing messy natural language into
  structure, unsuitable as an uncontrolled decision-maker.
- **Why TalentFlow uses them — and only for four things:** JD → structured
  requirements; resume → structured profile; screening questions; and
  (as embeddings) semantic similarity. Everything judgement-like is
  deterministic code.
- **Where:** `backend/app/ai/` — never imported outside it. The provider
  interface (`ai/base.py`) means the rest of the system doesn't know or care
  whether a model or the mock produced the data.
- **Without them:** the mock provider still runs the whole product (that's the
  point); extraction quality on unusual documents would drop sharply.
- **Interview line:** "The interesting engineering decision is where NOT to
  use the LLM. Matching a candidate to requirements is not a prompt — it's a
  deterministic function you can unit-test, audit line by line, and explain to
  a hiring manager."

## 11. Structured outputs

- **What it is:** asking a model to return JSON that must match a schema you
  supply, enforced by the API (not by hoping the prompt works).
- **Why TalentFlow uses it:** extraction is a data pipeline, not a chat.
  TalentFlow calls the OpenAI Responses API with
  `text_format=<PydanticModel>` — the response either satisfies the schema or
  errors; there is no "parse the model's prose" step anywhere.
- **Where:** `backend/app/ai/openai_provider.py` (`client.responses.parse`),
  schemas in `backend/app/ai/schemas.py`.
- **Without it:** regex-scraping JSON out of free text — brittle, and the
  "validated before persistence" claim would be unenforceable.
- **Interview line:** "The prompt sets semantics; the schema enforces shape;
  Pydantic + the normalization layer enforce sanity. Three gates before the
  database sees anything."

## 12. Embeddings

- **What it is:** mapping text to a numeric vector such that similar meanings
  land near each other; cosine similarity between vectors approximates
  semantic relatedness.
- **Why TalentFlow uses them:** as a *supporting signal* — overall text
  similarity between a candidate's profile and the job, and semantic hints for
  soft requirements. Never as the decision.
- **Where:** `backend/app/ai/embeddings.py` (OpenAI provider +
  deterministic hashed mock), chunking in
  `backend/app/services/embeddings_store.py`.
- **Without them:** matching still works (it's deterministic-first) — you'd
  lose the similarity column in the UI and semantic evidence hints.
- **Interview line:** "Embeddings are stored per text chunk with the chunk
  text itself, so any semantic hit can be shown back to the recruiter as a
  quotable snippet — not a black-box number."

## 13. pgvector

- **What it is:** a PostgreSQL extension adding a `vector` column type and
  distance operators (`<=>` cosine distance) with ANN indexes (HNSW) for fast
  nearest-neighbour search.
- **Why TalentFlow uses it:** embeddings live next to the relational data;
  similarity search is a SQL query (`ORDER BY embedding <=> CAST(:q AS
  vector) LIMIT k`) using the HNSW index — production-shaped, no second
  system to run.
- **Where:** column type in `backend/app/models/embedding.py`; extension +
  `CREATE INDEX … USING hnsw (embedding vector_cosine_ops)` in
  `backend/alembic/versions/3dc9b96a8fcf_initial_schema.py`; query in
  `backend/app/services/embeddings_store.py::search_similar`.
- **Without it:** you'd ship embeddings to a separate vector database —
  another service, another consistency problem, for demo-scale data.
- **Interview line:** "The dialect difference is quarantined: one type
  decorator and one search function know pgvector exists; on SQLite the same
  feature falls back to in-process cosine so dev and tests need no server."

## 14. Semantic similarity

- **What it is:** using embeddings to measure meaning-level closeness between
  two texts (what TalentFlow reports as text similarity between a profile and
  a job).
- **Why TalentFlow uses it:** recruiters read it as a soft signal ("the
  profile reads like this role"); it also powers evidence hints when a
  requirement is phrased loosely. It is explicitly *not* allowed to override a
  deterministic evaluation.
- **Where:** `_overall_similarity` in `backend/app/services/matching.py`;
  displayed per match card and overall in the UI.
- **Without it:** the product still works; you lose a supporting signal and
  the mock-mode approximation is one less thing to explain.
- **Interview line:** "The hard rule is asymmetry: a high similarity can
  *support* evidence, but a missed must-have stays missed no matter how
  similar the texts are. The LLM never gets a vote on the verdict."

## 15. Skill normalization

- **What it is:** mapping surface forms to canonical names — "JS", "Node.js",
  "k8s", "Postgres" → `javascript`, `node.js`, `kubernetes`, `postgresql` —
  plus small curated families that relate different-but-adjacent skills.
- **Why TalentFlow needs it:** extraction is noisy and recruiters write JDs
  freely; without normalization, "React" and "React.js" never match and every
  coverage number is wrong.
- **Where:** `backend/app/services/skills.py` (lexicon, aliases, categories,
  families) used by the mock extractor, the normalizer, and the matching
  engine's related-skill partial credit. Boundary-precision matters: the
  alias `js` must NOT fire inside "Node.js" (regression-tested).
- **Without it:** string-equality matching — a demo-killer. And this is the
  most recruiter-legible part of the engineering: it encodes how a human TA
  actually reads a resume.
- **Interview line:** "It's a curated, editable data table — precision over
  recall by design. A related skill can downgrade a hard miss to *partial*,
  but it can never mark a missing skill as met."

## 16. Candidate matching (the explainable engine)

- **What it is:** evaluating each job requirement against the candidate's
  profile and reporting coverage, gaps and evidence.
- **Why built deterministic-first:** ranking people is high-stakes and
  regulated; an opaque score invites bias and is undebuggable. TalentFlow's
  engine returns `met/partial/missing/unknown` **with written reasons and
  quoted evidence**, and a composite whose formula is printed right next to it
  (`0.60·must_have + 0.20·preferred + 0.10·experience + 0.10·domain`,
  re-normalized over present components).
- **Where:** `backend/app/services/matching.py` (+ `matching_evidence.py`);
  rendered by `frontend/src/components/matching/MatchCard.tsx`.
- **Without this design:** you'd have a prompt ("is this candidate good?") — a
  number nobody can audit, the exact thing this project exists to argue
  against.
- **Interview line:** "Every number in the UI can be re-derived by hand from
  the rows above it. That's the acceptance test for 'explainable'."

## 17. Prompt engineering

- **What it is:** designing the system/user instructions so a model performs a
  narrow task reliably.
- **Why TalentFlow cares:** prompts are the semantic half of the structured
  contract — they define must-have vs preferred detection, canonical skill
  naming, evidence sentences, and they hard-exclude protected characteristics.
  Resumes/JDs are wrapped as *data* (`<resume>…</resume>`) with instructions to
  ignore embedded directives (prompt-injection hygiene).
- **Where:** `backend/app/ai/prompts.py` (all prompts, versioned in git).
- **Without careful prompts:** schema-valid but semantically wrong extractions
  — the failure mode structure alone can't catch.
- **Interview line:** "Treat every document as hostile input: delimit it,
  forbid it from being instructions, validate the output shape, then
  normalise the content. Four layers between a stranger's PDF and my
  database."

## 18. CI/CD

- **What it is:** automated verification and delivery pipelines on every push.
- **Why TalentFlow has CI:** a portfolio claim is only as good as its
  reproducibility — CI proves the suite, the migrations and the Docker builds
  pass on a clean machine, including against a real PostgreSQL+pgvector.
- **Where:** `.github/workflows/ci.yml` — three jobs: backend (ruff + full
  pytest against a pgvector service container, frozen lockfile), frontend
  (npm ci → eslint → tsc → vitest → production build), docker (`compose
  config` + build all images).
- **Without it:** "works on my machine" — and reviewers stop trusting green
  checkmarks that don't exist.
- **Interview line:** "The pgvector integration test runs against a real
  Postgres in CI, and I ran the same clean-start locally with Docker volumes
  wiped — the migration and extension actually execute, not just compile."

## 19. Testing

- **What it is:** executable verification — unit, API/integration, and
  end-to-end layers.
- **Why TalentFlow has 94 backend + 18 frontend tests (91% coverage):** the
  product's core claims are behavioral — "evidence quotes real text",
  "related skills can't become met", "no protected columns exist", "stage
  moves always audit". Those are tests, not promises. The suite is hermetic
  (in-memory SQLite + mock providers, no network), so it runs anywhere,
  and the PostgreSQL integration test covers the other dialect.
- **Where:** `backend/tests/*` (12 modules), `frontend/src/**/*.test.ts(x)`,
  acceptance checklist in `TESTING.md`.
- **Without tests:** the explainability guarantees would be aspirational and
  the audit (which caught three real bugs) impossible.
- **Interview line:** "I test the claims a reviewer would challenge — the
  structural guard that no protected-attribute column can exist walks the
  whole schema and fails the build if someone adds one."

## 20. Responsible AI

- **What it is:** designing AI systems so they don't launder bias or hide
  their reasoning — and proving it in code, not slogans.
- **Why it's mechanical here:** protected characteristics have no columns
  anywhere (structurally tested), prompts exclude them, screening questions
  are category-restricted, matching never infers them, and the platform never
  emits hire/no-hire. The recruiter always decides; every AI judgement is
  labeled (mock vs live) and traceable to quoted evidence.
- **Where:** `RESPONSIBLE_AI.md` (the contract),
  `backend/tests/test_matching_engine.py` (the guard), prompts, and the
  health page's honest mode reporting.
- **Without it:** you'd be shipping the thing this project critiques.
- **Interview line:** "In TA tooling, 'the AI recommended it' is not a
  defence. Everything TalentFlow shows is evidence a human can disagree
  with — which is exactly what makes it legally and ethically defensible."

---

## Closing: how to tell the story (2 minutes)

> "TalentFlow AI is an open-source recruiting platform I built end-to-end:
> Next.js UI, FastAPI backend, PostgreSQL with pgvector, Docker. It ingests
> job descriptions and resumes — PDF, DOCX, TXT — into validated structured
> data using the OpenAI API with structured outputs, or a deterministic mock
> when there's no key, so anyone can run it. The part I'm proudest of is the
> matching engine: rather than an opaque AI score, it evaluates every
> requirement individually — met, partial, missing — and shows quoted
> evidence from the candidate's own resume with a fully published scoring
> formula. I tested the claims that matter: 94 backend tests including a real
> pgvector integration test against PostgreSQL, a structural test that no
> protected-attribute field can ever exist in the schema, and an
> end-to-end browser run of the whole hiring workflow. It's the tool I
> wanted as a recruiter, built the way I believe AI in hiring should be
> built: automation that assists a human who stays accountable."

## Rapid-fire answers you should have ready

- *Why is the score 0.60/0.20/0.10/0.10?* Priorities: must-haves dominate;
  the weighting is a documented, editable constant, re-normalized so missing
  requirement categories don't dilute the score.
- *Why not just ask GPT to rank candidates?* Untestable, unexplainable,
  biased by whatever the prompt didn't control — and the ranking would change
  with every model update. The engine is deterministic: same data, same
  result, auditable.
- *How do you stop prompt injection from a malicious resume?* Documents are
  delimited data with explicit "ignore instructions" system prompts; output
  must satisfy a strict schema; normalization caps and cleans everything; the
  resume is only ever rendered as escaped text.
- *What happens with no OpenAI key?* Full product, deterministic mock
  provider, every record labeled `extraction_method="mock"` in API, DB and
  UI — never disguised as model output.
- *Where would auth go?* Wrapping the service layer — it's the single
  mutation choke-point, so authz rules land in one place instead of 24
  endpoints.

