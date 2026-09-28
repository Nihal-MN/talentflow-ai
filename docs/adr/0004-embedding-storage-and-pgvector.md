# ADR 0004 — Embedding storage: pgvector on PostgreSQL, in-process cosine on SQLite

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

Semantic similarity needs vector storage and similarity search. The runtime
database is PostgreSQL where pgvector is the standard, indexable solution. The
zero-setup dev/test fallback is SQLite, which has no vector type. Both must work
against the same schema managed by the same migrations.

## Decision

- Embeddings live in a single table `embedding_records`
  (`owner_type`, `owner_id`, `chunk_index`, `chunk_text`, `embedding`).
- The `embedding` column is **`vector(1536)` on PostgreSQL** (pgvector
  extension created in the migration, HNSW index with `vector_cosine_ops`) and
  a JSON-encoded `TEXT` column on SQLite. A `TypeDecorator`
  (`app/models/embedding.py`) handles serialization per dialect.
- Both the OpenAI embedding model (`text-embedding-3-small`) and the
  deterministic mock embedder emit **1536-dim** vectors, so the column
  dimension never changes across modes.
- Similarity search is implemented once in
  `app/services/embeddings_store.py::search_similar`:
  - PostgreSQL → SQL `<=>` cosine-distance `ORDER BY ... LIMIT k` using the
    HNSW index;
  - SQLite → fetch candidate rows for the owner type and compute cosine in
    NumPy (dataset sizes here are demo-scale; this is documented, not hidden).
- Chunking: resumes are split into section-ish chunks (summary, experience
  bullets, skills); job descriptions into requirement-level chunks. Chunk text
  is stored so evidence is always traceable back to source text.

## Consequences

- Semantic search is indexable and production-shaped on the PostgreSQL path
  (exercised in Docker and in CI).
- The SQLite path keeps local dev and tests free of external services at the
  cost of an in-memory fallback for similarity — explicitly quarantined.
- Re-embedding is explicit and idempotent (delete-by-owner then insert), so
  switching providers mid-demo cannot mix vector spaces silently: the embedder
  name is recorded per record.
