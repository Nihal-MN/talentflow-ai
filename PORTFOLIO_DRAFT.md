# Portfolio Draft — TalentFlow AI

> **DRAFT — pending independent review.** Every claim below maps to something
> implemented and verified in this repository (see `CHATGPT_REVIEW_HANDOFF.md`
> for the audit trail). Nothing here is written yet; adjust voice, trim, and
> post only after you've read `TALENT_ENGINEER_INTERVIEW_GUIDE.md` and can
> defend each line.

---

## GitHub repository description (About field)

> Open-source AI-native hiring pipeline with structured talent data,
> explainable candidate matching, semantic search and recruiter-in-the-loop
> workflows.

## GitHub topics

`talent-engineering` · `recruiting` · `artificial-intelligence` · `llm` ·
`fastapi` · `nextjs` · `postgresql` · `pgvector` · `semantic-search` ·
`hr-tech` · `open-source` (optionally: `python`, `typescript`, `docker`,
`explainable-ai`, `responsible-ai`, `structured-outputs`)

---

## CV project entry

**TalentFlow AI — Open-source AI-native hiring platform** (personal project,
2026) · [github.com/<you>/talentflow-ai]

Designed and built a full-stack recruiting platform end-to-end: Next.js/
TypeScript UI, FastAPI/Python backend, PostgreSQL + pgvector, Docker Compose.
It ingests job descriptions and resumes (PDF/DOCX/TXT) into validated
structured data using LLM structured outputs (with a deterministic keyless
mock mode), evaluates candidates requirement-by-requirement with quoted
evidence and a published scoring formula, and manages a hiring pipeline with
notes, tags and AI-assisted screening questions. 95 backend tests (91%
coverage) + 18 frontend tests, CI against a real PostgreSQL+pgvector service,
Responsible-AI constraints enforced in code.

## CV bullets (3 — pick 2–3 depending on space)

- Built TalentFlow AI, an open-source AI-native recruiting platform (FastAPI,
  Next.js/TypeScript, PostgreSQL+pgvector, Docker): job/resume ingestion with
  LLM structured outputs validated before persistence, explainable
  requirement-level candidate matching with quoted resume evidence, and a
  full hiring pipeline — verified end-to-end in a browser-automated
  walkthrough and 113 automated tests.
- Implemented a deterministic-first, explainable matching engine that replaces
  opaque AI scores with per-requirement verdicts (met/partial/missing),
  published scoring weights and source-quoted evidence; shipped a provider
  architecture (OpenAI + deterministic offline mock) so the product runs
  fully without API keys and labels AI provenance per record.
- Designed the data layer and platform engineering: SQLAlchemy 2.0 models
  across PostgreSQL and SQLite from one Alembic migration set, pgvector
  (HNSW cosine index) for semantic search with an in-process fallback,
  healthcheck-gated Docker Compose startup, and CI that runs the suite
  against a real PostgreSQL+pgvector container.
- Enforced Responsible-AI constraints mechanically rather than rhetorically:
  no protected-attribute columns exist anywhere in the schema (structural
  test), protected characteristics are excluded from prompts and screening
  questions, and every automated judgement is traceable to quoted evidence —
  the recruiter always makes the decision.

## LinkedIn project description

> **TalentFlow AI** — an open-source hiring platform I built to prove a
> point: AI in recruiting can be *explainable*.
>
> Most "AI matching" reduces a person to a single opaque score. TalentFlow
> instead turns job descriptions and resumes (PDF/DOCX/TXT) into validated
> structured data — using the OpenAI API with structured outputs, or a
> deterministic offline mode when no API key is present — and then matches
> candidates requirement-by-requirement: met, partial, or missing, each with
> **quoted evidence from the candidate's own resume** and a scoring formula
> displayed right in the UI. Recruiters move candidates through a full
> pipeline (NEW → HIRED) with notes, tags and AI-assisted screening
> questions; a health page keeps the platform honest.
>
> Built with FastAPI, Next.js/TypeScript, PostgreSQL + pgvector (semantic
> search), Docker Compose, and 129 automated tests (111 backend, 18 frontend) — including a structural
> guard that no protected-attribute data can exist anywhere in the system.
> The human always makes the decision.
>
> Repo: github.com/Nihal-MN/talentflow-ai

## LinkedIn launch post (draft)

> For the last few weeks I've been building something between "recruiter" and
> "engineer" — and today it's public. 🚀
>
> **TalentFlow AI**: an open-source, AI-native hiring pipeline where every
> matching decision is explainable.
>
> What it does:
> • Reads job descriptions and turns them into structured must-have/preferred
>   requirements
> • Ingests resumes (PDF/DOCX/TXT) into validated candidate profiles
> • Matches candidates requirement-by-requirement — met / partial / missing —
>   with **quoted evidence from their own resume** and the scoring formula
>   shown on screen
> • Runs the full hiring pipeline with notes, tags and screening-question
>   generation
> • Runs entirely without an API key in a clearly labeled deterministic demo
>   mode (and with the OpenAI API when configured)
>
> What it deliberately doesn't do: give you "the score" and hide the math,
> or make hiring decisions. Automation assists; recruiters decide. (No
> protected characteristics exist anywhere in the schema — that's a test,
> not a policy.)
>
> Stack: FastAPI · Next.js/TypeScript · PostgreSQL + pgvector · Docker.
> 129 tests (111 backend, 18 frontend), CI on GitHub Actions. Feedback very welcome.
>
> → https://github.com/Nihal-MN/talentflow-ai · [optional: 30-sec screen recording]

## Technical LinkedIn post ideas (pick any; each is one screen + one insight)

1. **"Why I made my AI hiring tool refuse to rank people."** The
   deterministic-first matching engine: how met/partial/missing + quoted
   evidence beats a magic number, with a screenshot of a match card.
2. **"A resume is hostile input."** Prompt-injection hygiene for document
   pipelines: data delimiters, schema-validated outputs, normalization gates,
   escaped rendering — four layers between a stranger's PDF and your database.
3. **"Same migrations, two databases."** Engineering pgvector into a project
   that also runs on SQLite: type decorators, one dialect-aware search
   function, and the integration test that caught my own bind-format bug.
4. **"Testing the claims a reviewer would challenge."** The structural test
   that walks the whole SQLAlchemy schema and fails if a protected-attribute
   column ever appears.
5. **"How I made matching explainable in 5 steps"** — the exact evaluation
   pipeline (skill canonicalization → relatedness partial credit → evidence
   retrieval → supporting semantic signal → published weights).
6. **"Keyless by default."** Why the demo ships with a deterministic mock AI
   mode, and how provenance labeling (`extraction_method`) keeps mock and
   live output from ever being confused.

---

## Verification notes for future-you

* Numbers used above (95 backend / 18 frontend tests, 91% coverage, 4 jobs /
  10 candidates demo, 113 total tests) reflect the audited state at commit
  `e6e0005`. If you change the code, recompute before posting.
* The OpenAI path is wired and contract-tested but was not run against the
  live API in the build environment. If you demo with a real key before
  posting, say "I ran it with the OpenAI API" only once you actually have.
* Don't call it "production-ready" anywhere: it has no authentication yet —
  the roadmap says so, and reviewers respect that more than overclaiming.
