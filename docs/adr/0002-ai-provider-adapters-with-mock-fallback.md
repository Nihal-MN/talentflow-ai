# ADR 0002 — AI provider adapters with a deterministic mock fallback

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

The product's intelligence features (structured JD/resume extraction, screening
questions, embeddings) depend on an external LLM API. Reviewers and CI may have
no API key, tests must be deterministic, and an external outage must never take
the application down. At the same time the project must genuinely demonstrate
the OpenAI API with structured outputs — a "fake" implementation presented as
real would be dishonest.

## Decision

- All LLM and embedding usage goes through two small interfaces
  (`LLMProvider`, `EmbeddingProvider`) defined in `app/ai/base.py`.
- **Two real implementations:**
  - `OpenAILLMProvider` — current OpenAI SDK, structured outputs validated
    against the same Pydantic models used for DB persistence, plus embeddings.
  - `MockLLMProvider` — a deterministic, offline, rule-based extractor
    (lexicon + pattern matching). Its outputs logically mirror the OpenAI
    schema, so the rest of the system cannot tell the difference. It is clearly
    labeled as `mock` everywhere it is surfaced (API responses, System Health).
- `AI_PROVIDER=auto` (default) selects OpenAI **iff** `OPENAI_API_KEY` is set,
  otherwise the mock. `openai` forces the API; `mock` forces offline.
- LLM output never becomes database truth directly: every response passes
  Pydantic validation + a normalization layer before persistence.
- Mock behavior is a deterministic function of input text — same input, same
  output, every run.

## Consequences

- The demo, tests and visual acceptance run are fully hermetic; CI needs no
  secret.
- The OpenAI path is exercised by unit tests using an injected stubbed client,
  so wiring (prompt → schema validation → persistence) is tested even without
  a key. Real-model extraction quality is only observable with a key — called
  out in documentation.
- Anything that mixes mock and OpenAI data is labeled per-record
  (`extraction_method`), so a reviewer always knows the provenance.
