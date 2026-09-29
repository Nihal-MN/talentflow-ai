# Contributing to TalentFlow AI

Thanks for wanting to help. This is a portfolio-scale project with
production-minded standards — small, complete, tested.

## Ground rules

1. **Never contribute real candidate data.** All example/demo content must be
   synthetic (fictional names, `@example.com` emails, 555-style phone numbers).
   PRs containing real PII will be closed.
2. **Explainability is a contract.** Any change to scoring must keep results
   traceable: statuses with written reasons, quoted evidence, published
   weights. PRs that introduce opaque scores will be rejected (see
   `RESPONSIBLE_AI.md`).
3. **No protected characteristics, ever** — not in schemas, not in prompts,
   not in matching, not in tests' fixtures.
4. **`main` stays green.** All tests + linters must pass locally before a PR.

## Prerequisites

* Python 3.12+ with [uv](https://docs.astral.sh/uv/) for the backend
* Node 20+ with npm for the frontend
* Docker (any daemon — Docker Desktop, Colima, remote) only for the full-stack path

## Development setup

```bash
cp .env.example .env
cd backend  && uv sync && uv run alembic upgrade head && cd ..
cd frontend && npm install && cd ..
make dev          # API + web together, or use Docker: make up
```

## Before you push

```bash
make test         # backend pytest + frontend vitest + typechecks
make lint         # ruff + eslint
```

Backend formatting is enforced by **ruff** (line length 100). Frontend uses
**eslint** (Next core-web-vitals + TypeScript rules) and strict `tsc`.

## How to add a provider

Implement the `LLMProvider` / `EmbeddingProvider` protocol from
`backend/app/ai/base.py`, return the shared dataclasses, and register it in
`backend/app/ai/factory.py`. Add tests using an injected fake client — the
suite must stay network-free and key-free.

## How to extend matching

* New requirement categories: add the evaluation function in
  `services/matching.py`, wire it into `_evaluate_requirement`, and update
  `_components` if it should affect the composite score.
* Every new status/behavior needs a test that proves the guarantee (e.g.
  "related skills can never produce `met`").
* Keep weights transparent: `WEIGHTS` is a published constant.

## Database changes

Schema changes go through Alembic, never `create_all` in application code:

```bash
cd backend
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head && uv run alembic check   # no drift
```

Migrations must work on both PostgreSQL and SQLite (see `docs/adr/0004` for
the pattern used by the embedding column).

## Branch naming

Short-lived branches off `main`, one topic each:

`feat/<topic>` · `fix/<topic>` · `docs/<topic>` · `test/<topic>` · `chore/<topic>`

## Commit style

Conventional-commit-ish prefixes (`feat:`, `fix:`, `test:`, `docs:`, `chore:`)
with a short imperative subject. Small, focused commits over giant ones.

## PR checklist

- [ ] Tests added/updated; `make test` green locally
- [ ] `make lint` clean
- [ ] No secrets, no real PII, no `.env` files
- [ ] Docs updated when behavior/contracts changed (`docs/API.md`, `docs/ARCHITECTURE.md`,
      `docs/AI_DESIGN.md`, `RESPONSIBLE_AI.md` as applicable)
- [ ] UI changes include empty/loading/error states and keep the evidence
      views intact

## Opening an issue / a PR

* Bug reports and feature requests use the issue templates — fill in the
  fields; they exist so we can help without a round-trip. For anything
  larger than a small fix, open an issue first so we can agree on the
  approach before you write code.
* PRs should be small, reference the issue (`Closes #12`), fill in the
  PR template (GitHub pre-fills it), and include tests for behavior
  changes.

## What review looks like

A maintainer runs the suite on your branch, checks that the
explainability and responsible-AI guarantees still hold, and leaves
specific, actionable comments. Expect a first response within days —
if there's silence, a polite ping on the PR is welcome. Approved PRs
are squash-merged into `main`.

## Good first issues

* Extend the skill lexicon (`backend/app/services/skills.py`).
* Add more synthetic candidates/jobs to the demo dataset.
* Improve empty-state copy or accessibility labels in the frontend.
* Add a screening-question category with tests.
