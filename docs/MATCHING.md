# Matching Engine — TalentFlow AI

How candidates are evaluated against job requirements, exactly as implemented in
`backend/app/services/matching.py` (+ `matching_evidence.py`). Every claim here
maps to code; the acceptance tests live in `backend/tests/test_matching_engine.py`.

**One-sentence summary:** deterministic requirement-by-requirement evaluation
with quoted evidence and a published scoring formula — semantic similarity is a
*supporting* signal that can never override a deterministic result.

---

## 1. Why deterministic-first

Ranking people is high-stakes. An opaque "AI score" is untestable,
unexplainable when challenged, and changes when the model version does. So the
engine is ordinary, auditable Python: same inputs → same outputs, every number
re-derivable by hand from the rows shown in the UI. The LLM's role is upstream
(parsing documents into structured data) and advisory (semantic evidence
hints); it never evaluates requirements and never produces the score.

## 2. Inputs

- **Job requirements** — rows extracted from the JD
  (`job_requirements` table): `kind` (`must_have`/`preferred`), `category`
  (`skill`/`experience`/`education`/`location`/`domain`/`other`), label, and
  structured fields (canonical skill, `min_years`, degree level, location).
- **Candidate profile** — normalized: canonicalized skills (each with the
  verbatim evidence line from the resume), dated experience entries, education,
  computed years of experience, location, domain signals, and the chunked
  resume text with embeddings.

## 3. Evaluation pipeline (per requirement)

```
For each requirement:
  1. dispatch on category → evaluate skill / years / education / location / domain
  2. produce status + written reason + evidence list
Statuses: met · partial · missing · unknown · advisory
```

### 3.1 Skill requirements

1. Candidate skill names are canonicalized through the same
   `normalize`/`canonicalize` layer used at ingestion (so "JS", "Node.js"
   and "TypeScript" variants line up with the requirement's canonical name).
2. **Exact canonical match** → `met`, reason "Skill 'x' is present in the
   candidate's profile.", evidence = the quoted resume line(s).
3. **No exact match, but a family-relative skill exists** (curated families in
   `services/skills.py`, e.g. `keras`↔`tensorflow`) → `partial`, with the
   related skill(s) named in the reason and quoted. Related skills can only
   *downgrade a miss to partial* — they can never fake a `met`.
4. Neither → `missing`, reason names the absent skill.

### 3.2 Experience (years)

- Years come from **dated roles, merged ranges** (overlaps not double-counted).
- `years ≥ required` → `met`; within **1.5 years below** (`PARTIAL_YEARS_TOLERANCE`)
  → `partial` ("0.8 years short — close"); otherwise `missing`.
- Evidence is a **computed statement** (e.g. "7.2 years across 2 dated roles,
  computed from resume dates") — explicitly labeled computed, never passed off
  as a quote.

### 3.3 Education

- Degree synonyms are expanded (`BSc` ≈ "Bachelor's" ≈ "Bachelor of Science");
  level ordering compares attained vs required. Evidence quotes the education
  line.

### 3.4 Location

- Word-boundary matching on city/country tokens (so "Rome" never matches
  inside "Remote"; the substring bug is regression-tested). "Remote"-friendly
  JDs get their own handling.

### 3.5 Domain & other

- Domain requirements check the candidate's domain/industry signals; `other`
  free-text requirements may fall through to `unknown` (see below) rather than
  guessing.

### 3.6 `unknown` and `advisory`

- `unknown` — the requirement couldn't be confidently evaluated from the
  data (e.g. a soft, unstructured phrasing). Unknown is excluded from
  score components; it is surfaced to the recruiter instead of silently
  treated as a miss.
- `advisory` — soft requirements where the recruiter's judgement matters;
  may receive a semantic hint (below) but never a hard verdict.

## 4. Evidence — everything is traceable

Two evidence shapes exist and are visually distinguished in the UI:

| Shape | Source | Guarantee |
|---|---|---|
| **Quoted snippet** | verbatim text from the candidate's resume | the substring must actually occur in the stored resume text — evidence cannot be invented by the model or the engine |
| **Computed statement** | engine arithmetic (years across roles, etc.) | labeled "computed"; reproducible from dated entries |

**Semantic hints (soft requirements only):** when embeddings exist, a chunk of
resume text with cosine similarity ≥ **0.35** (`SOFT_EVIDENCE_SIMILARITY`) can
be attached to an `advisory` evaluation as a hint. Hints never upgrade a
status; they only help a human look in the right place.

## 5. Composite score — the exact formula

```
component score  = Σ status_scores(considered evaluations) / count
                   status_scores: met = 1.0 · partial = 0.5 · missing = 0.0
components: must_have · preferred · experience · domain
weights:        0.60       0.20    0.10    0.10

composite = 100 × Σ (weight[c] / Σweights_present) × component[c]
```

- Weights are **re-normalized over present components** (a job with no domain
  requirement doesn't get punished — that weight redistributes).
- Rounded to 1 decimal (e.g. `75.0`); component percentages rounded to 4.
- The UI renders the full substitution, e.g.
  `0.60·must_have[75%] + 0.20·preferred[50%] + 0.10·experience[100%] + 0.10·domain[100%] = 75/100`.
- **Text similarity** (profile ↔ job embedding, cosine, 0–1) is shown as a
  supporting signal and is *not* part of the composite.
- Every result carries `engine_version` (`matching-engine-v1`) so future
  changes to the engine are distinguishable in stored results.

The weights are a **documented heuristic**, not a law of nature: 0.60/0.20/
0.10/0.10 encodes "must-haves dominate". They are constants in one file —
change them and explain why in a PR.

## 6. Ranking & determinism

- Candidates are ranked by composite (descending); stable ordering and
  deterministic tie-breaks mean the same dataset always renders the same
  order. No randomness, no model calls at query time.
- Coverage counts per kind (met/partial/missing) are returned alongside so a
  recruiter can filter on *must-have misses* even when the composite is high.

## 7. Related-skill partial credit — why and its limits

Recruiters do this mentally ("no Kubernetes, but strong Docker and ECS in the
same ecosystem"). The engine encodes that as curated **families** in one
editable table. Limits, stated honestly: families are hand-curated and
incomplete; they are opinionated; and the mechanism is deliberately
asymmetric — *partial credit for adjacency, never false positives for
exactness*.

## 8. Limitations (read these before trusting any number)

- The skill lexicon is **precision-over-recall, English-centric**; unusual
  spellings may be missed. It is a data table, trivially extensible.
- Years-of-experience is date arithmetic over resume-declared ranges, not
  verified history.
- The composite is a **summarization of explicit judgements**, useful for
  ordering and for explaining — it is not an assessment of a person.
- In keyless mock mode, "similarity" is hashed-ngram approximation, not
  learned semantics; live mode uses `text-embedding-3-small`.
- No protected characteristics exist anywhere in this pipeline (structurally
  enforced — see [RESPONSIBLE_AI.md](../RESPONSIBLE_AI.md)).

## 9. Verify it yourself

```bash
cd backend && uv run pytest tests/test_matching_engine.py tests/test_matching_api.py
```

That suite covers: every status path, related-skill partials, evidence
quotability (the quoted-substring invariant), weight re-normalization, the
protected-columns structural guard, and regressions for previously fixed
bugs (the `js`-inside-`Node.js` alias bug, substring city matching).
