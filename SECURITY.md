# Security Policy — TalentFlow AI

## Supported versions

This is a demo/portfolio project: security fixes target the `main` branch only.

## Reporting a vulnerability

Open a **private** security advisory via GitHub
(`Security → Report a vulnerability`) rather than a public issue. Include steps
to reproduce. You can expect an acknowledgement within a few days. Please do
not include real candidate data in any report.

## Threat model & defenses

### 1. Untrusted documents (resumes / JDs)

Resumes and job descriptions are hostile-by-default input.

| Threat | Defense |
|---|---|
| Malicious file exploiting a parser | Only well-maintained, narrow parsers (`pypdf`, `python-docx`); size cap (10 MB) before parsing; failures raise a typed, user-safe error |
| Decompression bombs / huge text | Upload cap + extracted-text cap (200k chars) + per-field length caps in normalization |
| Prompt injection ("ignore previous instructions…") | Documents are wrapped as *data* with explicit delimiters; system prompts state that embedded instructions must be ignored; extraction output is schema-validated, so injected prose cannot alter structures |
| HTML/script injection via resume text | Resume text is rendered escaped (`<pre>`, React text nodes); no `dangerouslySetInnerHTML` anywhere |
| XSS via API error detail | Errors are rendered through the same typed client; no raw-HTML sinks |
| SQL injection | SQLAlchemy parameter binding everywhere (there is no raw string SQL except fixed DDL in the migration); a test searches with quotes in input |

### 2. Secrets

* Keys live only in environment variables / local `.env` (git-ignored).
* The API never returns key material; System Health reports only a boolean
  "configured" state.
* Logs never contain bodies, keys or candidate field values — the request
  logger records method/path/status/duration only.
* `.env.example` contains placeholders only; CONTRIBUTING forbids committing
  `.env`.

### 3. Data protection (PII-aware by design)

* The repository ships **synthetic-only** demo data; real candidate PII must
  never be committed (enforced by review; examples use `@example.com`).
* The schema minimizes sensitive surface: no protected characteristics, no
  national IDs, no photos (a test enforces the absence of such columns).
* Uploads are stored under a git-ignored `uploads/` volume with random
  prefixes; deleting a candidate removes their rows, applications, notes and
  embeddings.
* A deployed instance is a controller of whatever data you put into it —
  apply your jurisdiction's retention rules; nothing here is legal advice.

### 4. Application surface

* **No authentication in the demo.** Do not expose it to the public internet
  as-is; adding authn/authz is a documented pre-deployment step (see
  `PRODUCT.md` roadmap and ADR context). The service layer is intentionally the
  single mutation choke-point, so an auth layer can wrap it cleanly.
* CORS is an explicit allow-list (`CORS_ORIGINS`), not `*`.
* Request bodies are schema-validated (Pydantic) before reaching services;
  unknown fields are ignored; all mutations flow through services where
  ownership/status rules live.
* Error responses are structured and information-bounded (no stack traces,
  no SQL, no file paths).

### 5. Dependencies & CI

* Backend dependencies are pinned in `uv.lock`; frontend in
  `package-lock.json`; CI installs frozen (`uv sync --frozen`, `npm ci`).
* CI runs on every push/PR (lint, tests against PostgreSQL+pgvector, Docker
  builds). Dependabot-style upgrades are encouraged via PR.

### 6. Out of scope for the demo (documented honestly)

* Rate limiting / abuse protection at the edge (use a reverse proxy).
* File-type fingerprinting beyond extension + parser safety.
* Multi-tenant isolation (single-tenant by design in the demo).

## 7. Audit results (28 Sep 2026, full-repository review)

| Check | Method | Result |
|---|---|---|
| Secrets in git history | scanned every commit diff for `sk-…` / AWS-key patterns | **none found** |
| Committed environment files | tracked-file listing | only `.env.example`; real `.env` is git-ignored and untracked |
| Hardcoded credentials | grep for password/api_key/secret literals in app code | none |
| TODO/FIXME/placeholder leftovers | grep across app, tests, docs, CI | none in our code |
| Untracked local artifacts | `git status --ignored` | local DBs/uploads/caches all covered by `.gitignore` |
| Upload handling | code review + tests | extension allow-list, 10 MB cap, 200k-char text cap, parser isolation, typed user-safe errors (`test_documents.py`, `test_candidates_api.py`) |
| SQL injection | code review | SQLAlchemy parameter binding everywhere; the only raw SQL strings are fixed DDL in the migration and the pgvector `<=>` expression with bound parameters; a matching test searches with quote-laden input |
| PII in logs | code review | request logger records method/path/status/duration only; no bodies |
| CORS | config review + live check | explicit origin allow-list (`CORS_ORIGINS`), credentials disabled |
| Dependency hygiene | import sweep | unused `email-validator`/`httpx` removed; lockfiles frozen in CI |
| Secret exposure via API | `test_health.py` asserts the health payload contains no key material; System Health shows only a boolean | pass |
