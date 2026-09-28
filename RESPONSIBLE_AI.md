# Responsible AI — TalentFlow AI

This document is a contract, not a slogan. It describes what the system does,
what it refuses to do, and how the engineering enforces it.

## Core commitment

> **TalentFlow AI assists recruiters with evidence. It does not make hiring
> decisions, and it is built so that discriminatory automation has nowhere to
> hide.**

## 1. Protected characteristics are excluded by construction

* **No schema, no storage.** No table contains columns for age, date of birth,
  gender, sex, ethnicity, race, nationality, religion, marital status,
  disability, photos or national identifiers. A test
  (`test_no_protected_attribute_columns_exist_anywhere`) walks the entire
  SQLAlchemy metadata and fails if such a column is ever added.
* **No inference.** The matching engine evaluates requirements against skills,
  experience, education, location, domain and certifications. It never
  computes, derives or proxies protected attributes (no graduation-year
  proxies, no name-origin analysis, no photo processing — none exist).
* **Prompts exclude them.** The OpenAI prompts instruct the model to skip
  protected characteristics entirely, even when they appear in the source
  document.
* **Screening questions exclude them.** Generated questions may probe skills,
  experience and gaps — never personal circumstances. The mock provider's
  templates and the OpenAI prompt both say so, and tests assert the question
  categories stay within `technical / experience / gap_probe / behavioral`.

## 2. Explainability is mandatory, not optional

* Every requirement evaluation returns `met / partial / missing / unknown /
  advisory` **plus a written reason**.
* `met` and `partial` verdicts carry **quoted evidence** that literally
  appears in the candidate's own resume text (or a computed, disclosed
  statement — e.g. total years from merged date ranges).
* The composite score exposes its formula, component values and (re-normalized)
  weights directly in the UI. There is no undisclosed model in the loop.
* Soft ("other") requirements are labeled `advisory`, excluded from the score,
  and presented as signals for human judgement.

## 3. The human decides

* The platform produces match *evidence*, not verdicts. No endpoint, UI
  element or data field emits a hire/no-hire recommendation.
* Stage changes (including rejection) require an explicit human action, and
  every move is recorded in an append-only audit trail with an optional note.
* Recruiter notes and tags are free-text human context shown alongside the
  machine signals — not inputs to scoring.

## 4. Data discipline

* **Synthetic-only demo data.** All example JDs, candidates, emails and phone
  numbers are fictional (`@example.com`, 555-style numbers). The repository
  never contains real candidate PII; CONTRIBUTING.md makes this a hard rule.
* **Untrusted content handling.** Resumes and JDs are treated as hostile
  input: parsed, never executed; rendered as escaped text; size- and
  length-capped; prompt-injection resistant by construction (data
  delimiters + instructions to ignore embedded directives).
* **PII-aware logging.** Request logs contain method, path, status and
  duration only — never document bodies or candidate fields.
* **Secrets stay in the environment.** No key is ever written to the database,
  exposed via the API, or displayed in System Health (which reports only
  whether a key is configured).

## 5. Honest AI labeling

* Every extracted record stores which provider produced it
  (`extraction_method` = `openai` | `mock`) and which model/version; the UI
  badges every profile, requirement list and screening set accordingly.
* The System Health page states plainly when the platform runs in
  deterministic mock mode and what turns on the real API.
* Mock and real embeddings are never mixed silently: stored vectors record
  their embedder (`openai:text-embedding-3-small` vs `mock:hashed-ngram-v1`).

## 6. Known limitations (stated, not hidden)

* The matching engine's skill lexicon (`app/services/skills.py`) is curated and
  English-centric; relatedness families are a small hand-built map. It errs
  toward *not* over-crediting — misses are shown as misses.
* Semantic similarity in mock mode approximates lexical overlap; it is not
  semantic understanding. With an OpenAI key it is real embedding similarity —
  still a supporting signal only.
* "Years of experience" is a computed approximation from resume dates (merged
  ranges), not a life history; overlapping roles are counted once.
* The demo runs without authentication — deploying it multi-user requires
  adding authn/authz first (see SECURITY.md).

## 7. How to verify these claims

* `backend/tests/test_matching_engine.py` — behavioral guarantees and the
  protected-columns structural guard
  (`test_no_protected_attribute_columns_exist_anywhere` walks the entire
  SQLAlchemy metadata and fails on any age/gender/ethnicity/religion/
  disability/marital-status/media column).
* `backend/tests/test_extraction_mock.py`, `test_normalization.py` — input
  handling, alias-boundary precision, and validation gates.
* `RESPONSIBLE_AI` mapping in the UI: matching page footer and screening
  panel both link to this document from the running app.
* **Audit re-verification (28 Sep 2026):** full-repository sweep found no
  protected-attribute fields in schemas, prompts, tests or demo data; the E2E
  run produced screening questions in categories
  `technical / gap_probe / experience / behavioral` only (asserted in
  `test_screening_api.py`); no question or rationale referenced personal
  circumstances; the composite formula is rendered verbatim in the UI.
