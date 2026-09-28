# ADR 0001 — Modular monolith, synchronous services, PostgreSQL runtime with SQLite dev fallback

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

TalentFlow AI is a portfolio-scale recruiting platform that must (a) demonstrate
real production patterns — PostgreSQL, pgvector, migrations, tests, CI — and
(b) be runnable by a reviewer with near-zero setup. Introducing microservices,
queues or Kubernetes would add operational surface with no product benefit at
this scale.

## Decision

- **One backend service** (FastAPI) with clear internal layering:
  `api (routers) → services (domain logic) → models/db`, with AI provider code
  isolated in `app/ai/` behind interfaces.
- **Synchronous SQLAlchemy 2.0** (`Session` pattern). FastAPI runs `def`
  endpoints in its threadpool; this is simple, debuggable and honest for the
  workload (CRUD + a handful of AI calls). No premature async.
- **Runtime database is PostgreSQL** (via Docker Compose, image
  `pgvector/pgvector`). For zero-setup local development and fast tests, the
  backend falls back to SQLite when `DATABASE_URL` is unset. The same Alembic
  migrations create both schemas.
- **Dialect-specific behavior is quarantined** in exactly one place: embedding
  storage/search (`app/services/embeddings_store.py` / `app/models/embedding.py`).

## Consequences

- `git clone → docker compose up --build` gives the full PostgreSQL + pgvector
  stack; `make setup && make dev` gives a fully working native setup with no
  external services.
- Two dialects must stay compatible. Guarded by tests that run on SQLite
  locally and on PostgreSQL in CI.
- If the product outgrows a single service, the service-layer boundaries make
  extraction possible without a rewrite.
