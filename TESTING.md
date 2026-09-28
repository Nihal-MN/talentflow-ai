# Testing — TalentFlow AI

## How to run everything

```bash
make test              # backend + frontend in one go

# backend (pytest + coverage)
cd backend
uv run pytest                              # 93 tests + 1 pg-vector integration test (skipped without PG)
uv run pytest --cov=app --cov-report=term  # coverage report (currently 91%)
uv run python scripts/smoke_api.py         # end-to-end flow — human-readable output

# frontend (vitest + strict TS)
cd frontend
npm test               # component + client tests
npm run typecheck      # tsc --noEmit
npm run lint           # eslint (Next core-web-vitals + TS rules)
```

## What is covered (backend)

| Area | Tests | Highlights |
|---|---|---|
| Health | `test_health.py` | liveness, dependency report, no secrets in payload, structured 404 |
| Jobs | `test_jobs_api.py` | extraction quality assertions (must/preferred split, years, degree), paste + upload, filters, update/delete, validation errors |
| Candidates | `test_candidates_api.py` | PDF/DOCX/TXT ingestion, structured profile assertions, evidence presence, notes/tags lifecycles, unsupported/empty file errors |
| Documents | `test_documents.py` | text extraction, encoding detection (UTF-8/16/latin-1), corrupt PDFs, sanitization, length caps |
| Mock extraction | `test_extraction_mock.py` | section detection, "Remote"≠"Rome", prose filtering, canonical skill aliases, determinism |
| Normalization | `test_normalization.py` | canonicalization, dedup, range clamps, invalid kind/category repair |
| Skill taxonomy | (in `test_normalization.py`) | aliases, categories, relatedness semantics |
| Matching engine | `test_matching_engine.py` | every status path, evidence traceability, weight re-normalization, determinism, ranking order, **protected-columns structural guard** |
| Matching API | `test_matching_api.py` | ranking order, score payload completeness, pair explainer, reverse ranking, 404s |
| Pipeline | `test_pipeline_api.py` | idempotent create, full audit trail, no-op moves, invalid stage 422, board grouping, activity feed |
| Screening | `test_screening_api.py` | generation, gap probes for missing must-haves, regenerate-replaces semantics, listing |
| Embeddings | `test_embeddings_and_migration.py` | determinism, similarity ordering, degenerate inputs, storage idempotency, dimension guard, **Alembic upgrade/downgrade round-trip** |
| PostgreSQL path | `test_postgres_path.py` | dialect-level DDL/bind checks + `<=>` SQL compile (always run) and a full pgvector integration test (runs with `DATABASE_URL` pointing at PostgreSQL) |

Frontend (`frontend/src/**/*.test.ts(x)`): formatting/state constants, API
client error shaping (structured errors, network failures, 204s, FormData vs
JSON), MatchCard rendering (score, formula, expandable evidence, pipeline
affordance), StageControls behavior (advance, reject, reopen), badge labels.

## CI matrix (`.github/workflows/ci.yml`)

| Job | What it proves |
|---|---|
| Backend | ruff clean + full pytest suite **against a real PostgreSQL + pgvector service container** (the integration test above runs there), frozen lockfile |
| Frontend | npm ci → eslint → tsc → vitest → production build |
| Docker | `docker compose config` validates; all three images build |

## Manual acceptance workflow

Executed against a live stack (screenshots in `docs/screenshots/`; the
sequence below is exactly what was run, including the bug it caught — see
"Found by acceptance" at the end):

1. Open `http://localhost:3000` → dashboard renders with live counts.
2. Create a job (paste a JD via `Jobs → Create job`, or upload a file).
3. Verify extracted requirements on the job page (must-have / preferred split,
   skill chips, `5+ yrs` chips).
4. Upload ≥ 3 resumes (PDF + DOCX + TXT) from `examples/resumes/` on
   `Candidates` — each row shows "done · Extracted: <name>".
5. Verify candidate profiles (skills with clickable evidence, timeline,
   education, certifications).
6. On `Matching`, select the job → ranked candidates with score breakdown,
   formula, coverage and quoted evidence.
7. Add a candidate to the pipeline from a match card.
8. Open the candidate → generate screening questions.
9. Move NEW → SCREENING → SHORTLISTED via the stage controls.
10. Add a recruiter note.
11. Hard-refresh: stage, note and questions persist (also verified via API).
12. `Pipeline` board shows the candidate under Shortlisted with full column
    counts.
13. `System Health` shows all-operational, DB latency, AI mode and counts.
14. `python -m app.seed --reset` loads the full demo dataset (4 jobs,
    10 candidates, 10 applications, notes, tags, question sets).

**Found by acceptance, fixed, covered:** the multi-file upload handler read
the *live* `FileList` after the input was cleared, silently dropping every
file after the first (`parsing…` forever). Fixed by snapshotting the list
(`Array.from`) before iterating; the candidates page tests and this checklist
now guard it.

## Coverage philosophy

We test *behaviors that are load-bearing claims* — explainability guarantees,
validation gates, audit trails, honest labeling — not line-count theater. The
91% coverage number is a byproduct of that, not the goal.
