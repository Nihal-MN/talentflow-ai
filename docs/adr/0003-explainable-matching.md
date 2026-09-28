# ADR 0003 — Explainable, deterministic-first matching; no opaque AI score

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

"AI candidate scoring" is exactly where hiring tools become dangerous and
unaccountable. A single opaque number invites automation bias: recruiters treat
the score as a decision instead of assistance. It is also poor engineering —
untestable, undebuggable and impossible to justify to a candidate.

## Decision

Matching is computed as a transparent, layered pipeline:

1. **Deterministic requirement evaluation** — every `JobRequirement` is
   evaluated against the candidate's normalized profile and receives a status:
   `met / partial / missing / unknown` with a machine-readable reason.
2. **Normalized skill matching** — a canonical skill lexicon maps aliases
   ("JS" → "javascript", "React.js" → "react"); a small curated
   family/relatedness map recognizes near-misses (e.g. Docker ≈ Kubernetes
   domain knowledge) and marks them `partial`, never `met`.
3. **Semantic similarity** — cosine similarity between requirement text and
   candidate chunks supports evidence retrieval and an overall text-similarity
   signal. It can never silently override a deterministic miss.
4. **Evidence extraction** — every `met`/`partial` requirement carries source
   evidence (quoted snippets from the candidate's own resume text, with the
   match type: lexical or semantic).
5. **Composition** — the composite score is a documented weighted formula of
   must-have coverage (60), preferred coverage (20), experience alignment (10)
   and domain alignment (10), re-normalized over categories that exist.
   The UI exposes the formula, the per-requirement inputs and the evidence.

Hard constraints:

- No protected characteristics are used, inferred, or stored for matching.
  (Also documented in `RESPONSIBLE_AI.md`.)
- The UI never presents a single "hire/no-hire" verdict; it shows coverage and
  evidence, and the human recruiter keeps the decision.
- Text used for semantic similarity is the same resume text shown to the
  recruiter — no hidden inputs.

## Consequences

- Matching is unit-testable and reproducible (deterministic given the same
  profile data).
- Scores can be re-derived and audited by a third party, which is the point.
- The composite is a heuristic. It is labeled as such; weights are configurable
  in one module and documented.
