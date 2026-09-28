# AI Design — TalentFlow AI

How the intelligence layer works, why it is shaped this way, and what it
deliberately does **not** do. Companion documents: `RESPONSIBLE_AI.md`
(principles), `docs/adr/0002` (provider adapters), `docs/adr/0003` (matching).

## 1. Principles

1. **Providers behind interfaces.** Nothing in the domain layer imports an AI
   SDK. `app/ai/base.py` defines `LLMProvider` and `EmbeddingProvider`; two
   real implementations exist (OpenAI and a deterministic mock) plus a factory
   (`AI_PROVIDER=auto|openai|mock`).
2. **Structured output is a contract.** Every model response must validate
   against a Pydantic schema (`app/ai/schemas.py`) before anything else sees
   it. There is no free-text parsing of model prose anywhere.
3. **Unvalidated output never becomes truth.** A normalization layer
   (`app/services/normalization.py`) canonicalizes, deduplicates and
   range-checks; invalid values are dropped, not trusted.
4. **Deterministic where possible.** The mock provider is a pure function of
   input text; the matching engine is deterministic; only the OpenAI provider
   is non-deterministic — and the system stays fully functional without it.
5. **Fail softly.** A provider outage returns a typed `503
   provider_unavailable` for the affected request; it never crashes the app,
   and it never silently fabricates results.

## 2. The provider interface

```python
class LLMProvider(Protocol):
    name: str                      # "openai" | "mock"
    model: str                     # e.g. "gpt-5.6-terra" | "deterministic-rules-v1"

    def extract_job(self, jd_text: str) -> ExtractedJob: ...
    def extract_candidate(self, resume_text, *, source_filename=None) -> ExtractedCandidate: ...
    def generate_screening_questions(...) -> list[ScreeningQuestionDraft]: ...

class EmbeddingProvider(Protocol):
    name: str; model: str; dim: int
    def embed(self, texts: list[str]) -> list[list[float]]: ...
```

Providers return plain dataclasses (`ExtractedJob`, `ExtractedCandidate`, …)
so services and tests never depend on any SDK's wire format.

## 3. OpenAI implementation (current API)

* **Structured outputs via the Responses API**:
  `client.responses.parse(model=…, input=[…], text_format=PydanticModel)` →
  `response.output_parsed`, guaranteed schema adherence.
* Prompts (`app/ai/prompts.py`) wrap untrusted documents in explicit data
  delimiters and instruct the model to treat any embedded instructions as data.
* Extraction guidance encodes the product rules: must-have vs preferred
  detection, `min_years` from "5+ years", canonical lowercase skill names,
  per-skill evidence sentences, no protected characteristics anywhere.
* Model defaults: `gpt-5.6-terra` (extraction), `text-embedding-3-small`
  (1536-dim embeddings). Both overridable via env (`OPENAI_MODEL`,
  `OPENAI_EMBEDDING_MODEL`).
* The client is **injectable** — unit tests exercise the full wiring
  (prompt → schema validation → dataclass conversion) with a stub client, so
  the OpenAI path is covered in CI without network access.

## 4. The deterministic mock (default without a key)

* `mock_jd.py` — section detection (must-have vs preferred, with colon-less
  headers), skill lexicon matching, years/degree/location/domain patterns,
  prose-paragraph filtering, word-boundary city detection (no "Rome" inside
  "Remote").
* `mock_resume.py` — contact block, summary, experience entries (header +
  date-range + bullets, both orders), current-role detection, education,
  certifications, canonicalized skills with evidence lines.
* `mock_provider.py` — screening questions grounded in matched/missing skills
  and seniority.
* Determinism: same bytes in → same structures out, always. Every record it
  produces is labeled `extraction_method="mock"` in the database and surfaced
  with a badge in the UI.

The mock is not a "fake AI" façade: it is the offline counterpart of the same
contract, exercised by ~25 dedicated tests, and it powers the whole demo, the
test suite and CI.

## 5. Embeddings & semantic similarity

* **Chunking** (`embeddings_store.py`): candidates → summary/role/skills/
  education chunks; jobs → overview + one chunk per requirement. Chunk text is
  stored with every vector so semantic hits remain traceable.
* **OpenAI path**: `text-embedding-3-small`, 1536-dim.
* **Mock path**: hashed token/bigram random projection (deterministic,
  1536-dim, L2-normalized) — cosine similarity approximates lexical overlap.
  Clearly labeled `mock:hashed-ngram-v1`.
* **Storage**: `vector(1536)` on PostgreSQL (HNSW index, cosine ops); JSON
  text on SQLite. One `search_similar()` function knows the difference.
* **Usage in matching**: the overall similarity (mean over job chunks of the
  best candidate-chunk cosine) is displayed as a *signal*; per-requirement
  similarity can surface supporting evidence for soft requirements. It can
  never change a deterministic `missing` into `met`.

## 6. The matching engine (explainability contract)

Already summarized in `ARCHITECTURE.md §4.3`; the AI-specific point:

* the engine is **deterministic-first by design** — the "AI part" (semantics)
  is demoted to a supporting signal precisely because opaque ranking is the
  failure mode this project exists to demonstrate against;
* composite weights are published (`WEIGHTS` constant), re-normalized over
  present components, and rendered with the raw formula in the UI;
* `engine_version` is stored in every result for auditability.

## 7. Evaluation & quality

* Unit tests assert *behavioral guarantees* (evidence must literally exist in
  source text; related skills never count as met; soft requirements never
  affect the score; identical inputs produce identical results).
* The demo dataset doubles as a smoke evaluation: seeded rankings are
  hand-checked (e.g. the DevOps specialist ranks first for the DevOps role,
  the frontend-only profile shows honest gaps for a full-stack role).
* With an OpenAI key, reviewers can re-run the seed and compare extraction
  quality per record — every row records which provider produced it.

## 8. Costs, limits, failure modes

* Documents are capped (10 MB uploads, 60k chars to the model, 200k chars
  stored); embeddings cap at 24 chunks/owner.
* Provider errors → typed 503 with the upstream message; retries are left to
  the caller by design (no hidden retry loops).
* The mock's precision-over-recall tradeoff is deliberate: unknown skills are
  kept as candidates rather than guessed; the lexicon is a single editable
  data table (`app/services/skills.py`).
