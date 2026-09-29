# Product — TalentFlow AI

What this product is, for whom, and what it is deliberately not.

## Personas

**Primary — the technical recruiter / talent partner.** Works 10–30 open roles,
lives in email and LinkedIn, screens resumes by hand. Needs to answer quickly:
*does this person actually meet the must-haves, and where is the proof?*

**Secondary — the hiring manager.** Wants a shortlist with reasons they can
defend to their team, and screening questions that surface gaps early.

**Tertiary — the talent-engineering reviewer (this project's audience).**
Wants to see how a modern AI-native recruiting tool is *engineered*: validated
data models, structured LLM output, explainable matching, tested pipelines.

## Jobs to be done

1. **"Turn this JD into a checklist."** Paste or upload any job description →
   structured must-have / preferred requirements.
2. **"Turn this pile of resumes into profiles."** Upload many files (PDF,
   DOCX, TXT) → validated structured candidate profiles with evidence.
3. **"Show me who fits — with proof."** Rank candidates for a role, showing
   coverage, gaps and the exact resume lines behind every claim.
4. **"Keep the pipeline honest."** Move candidates through stages with an
   audit trail; capture notes and tags so context survives.
5. **"Prep my screening call."** Generate candidate-specific questions that
   probe strengths and gaps — never personal circumstances.

## User journeys (all browser-testable)

* **JD → requirements:** Jobs → Create job → paste or upload → job page shows
  extracted requirement groups with skills/years/education chips.
* **Resumes → profiles:** Candidates → drop files → per-file extraction
  feedback → profile page (timeline, skills with clickable evidence, notes,
  tags, best-fit jobs).
* **Match → decide:** Matching → pick job → ranked cards (score breakdown +
  published formula + per-requirement evidence) → add to pipeline.
* **Pipeline → hire:** Pipeline board → move stages with recorded notes →
  System Health for operational truth.

## Product principles

1. **Evidence over scores.** A number without its derivation is noise. Every
   claim in the UI is drillable to source text.
2. **The recruiter is the decision-maker.** The product frames choices; it
   never recommends hire/no-hire.
3. **Honest automation.** AI-generated content is labeled per record; mock
   mode is visible; limitations are documented, not hidden.
4. **Synthetic by default.** A reviewer can explore every page without any
   real personal data existing anywhere.
5. **No fake metrics.** Every number shown (counts, latencies, coverage) is
   computed from the live database at request time.

## Scope

**In:** job/candidate ingestion and structured extraction; explainable
requirement-level matching with evidence; pipeline stages + audit trail;
notes/tags; screening-question generation; system health; synthetic demo mode.

**Out (deliberately):** authentication/multi-tenancy (documented as
pre-deployment work), interview scheduling, email integrations, resume OCR for
scanned documents, analytics dashboards beyond operational health. Scope is
kept small so the parts that exist are complete and testable.

## Success metrics (for the demo dataset)

* Extraction: seeded jobs yield ≥ 8 must-haves; all 10 resumes parse with
  name, contact, roles and ≥ 6 skills.
* Matching: domain specialists rank first for their role (DevOps engineer →
  DevOps job …); coverage counts reconcile with the requirement list shown.
* Pipeline: every stage move produces exactly one audit event.
* Health: `/health` reports `ok` for database and a truthful AI mode.

## The 2-minute demo script

1. Open the dashboard — note the counts and AI-mode card (mock mode is honest).
2. Jobs → the Senior Full Stack Engineer job → requirements that came out of a
   pasted JD, split must/preferred.
3. Candidates → upload `examples/resumes/amira_haddad.resume.pdf` and watch the
   profile materialize; click a skill to see its evidence line.
4. Matching → select the job → point at one candidate: score → component bars
   → formula → per-requirement statuses → open a "missing" requirement and show
   the written reason (no black box).
5. Add the candidate to the pipeline; open the board; move a stage; open
   System Health and show that every system reports truthfully.

## Roadmap

Near-term: authentication + workspaces; CSV export; richer evaluation
(reranking with the OpenAI provider); interview scheduling. Longer-term:
ATS/email integrations, OCR ingestion, multi-language skill taxonomy.
