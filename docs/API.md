# API Reference — TalentFlow AI

Base URL: `http://localhost:8000/api/v1` (Docker: same port; OpenAPI:
`/docs`, raw schema: `/openapi.json`).

All errors share one shape:

```json
{ "error": { "code": "not_found", "message": "Job 42 does not exist." } }
```

| code | HTTP | meaning |
|---|---|---|
| `validation_error` | 422 | schema/query validation failed (`detail` lists fields) |
| `ingestion_error` | 422 | document unreadable/unsupported/empty |
| `not_found` | 404 | entity does not exist |
| `conflict` | 409 | conflicting state |
| `provider_unavailable` | 503 | AI provider failed/unconfigured for this request |
| `network_error` | — | (client-side) API unreachable |

---

## System

| method | path | description |
|---|---|---|
| GET | `/health/live` | liveness probe → `{"status":"ok"}` |
| GET | `/health` | full report: db status/latency/dialect, AI mode/config, counts |

```bash
curl -s localhost:8000/api/v1/health | jq '.status, .database.latency_ms, .counts'
```

## Jobs

| method | path | description |
|---|---|---|
| GET | `/jobs?status=&q=&limit=&offset=` | list (cards with must/preferred/app counts) |
| POST | `/jobs` | create from pasted JD `{title?, company?, location?, employment_type?, jd_text}` |
| POST | `/jobs/upload` | multipart `file` (PDF/DOCX/TXT) + optional `title`, `company` |
| GET | `/jobs/{id}` | detail incl. extracted `requirements[]` and `applications[]` |
| PATCH | `/jobs/{id}` | update `{status?, title?, company?, location?}` |
| DELETE | `/jobs/{id}` | delete (cascades applications) |

```bash
curl -s -X POST localhost:8000/api/v1/jobs \
  -H 'Content-Type: application/json' \
  -d '{"title":"Senior Full Stack Engineer","jd_text":"...full JD text..."}' | jq '.requirements[0]'
# → { "id": 5, "kind": "must_have", "category": "skill", "label": "Expert-level Python and FastAPI",
#     "normalized_skill": "python", "min_years": null, "keywords": ["python"] }
```

## Candidates

| method | path | description |
|---|---|---|
| GET | `/candidates?q=&skill=&limit=` | list (skills chips, years, applications count) |
| POST | `/candidates/upload` | multipart `file` → structured profile (201) |
| GET | `/candidates/{id}` | full profile: experiences, education, skills (with evidence), certifications, notes, tags, applications |
| DELETE | `/candidates/{id}` | delete (cascades; embeddings removed) |
| POST | `/candidates/{id}/notes` | `{body, author?, job_id?}` |
| DELETE | `/candidates/{id}/notes/{note_id}` | remove a note |
| POST | `/candidates/{id}/tags` | `{name, color?}` — creates the tag when new |
| DELETE | `/candidates/{id}/tags/{tag_id}` | detach a tag |

## Applications & pipeline

| method | path | description |
|---|---|---|
| GET | `/applications?job_id=&candidate_id=&stage=&limit=&offset=` | list (candidate+job embedded) |
| POST | `/applications` | `{candidate_id, job_id, note?}` — idempotent per pair (201) |
| GET | `/applications/board?job_id=` | `{ "NEW": [...], "SCREENING": [...], … }` |
| GET | `/applications/activity?limit=` | recent stage moves (dashboard feed) |
| GET | `/applications/{id}` | detail incl. `stage_events[]` audit trail |
| PATCH | `/applications/{id}/stage` | `{to_stage, note?}` — recorded event; same-stage = no-op |
| DELETE | `/applications/{id}` | remove from pipeline |

## Matching

| method | path | description |
|---|---|---|
| GET | `/matching/job/{job_id}?limit=&only_applicants=` | ranked candidates for a job |
| GET | `/matching/candidate/{candidate_id}?limit=` | ranked open jobs for a candidate |
| GET | `/matching/pair?job_id=&candidate_id=` | explain one pair |

Result shape (abridged):

```json
{
  "candidate_id": 1, "candidate_name": "Amira Haddad",
  "composite_score": 90.0,
  "components": { "must_have": 1.0, "preferred": 0.5, "experience": 1.0, "domain": 1.0 },
  "weights_used": { "must_have": 0.6, "preferred": 0.2, "experience": 0.1, "domain": 0.1 },
  "formula": "0.60·must_have[100%] + 0.20·preferred[50%] + … = 90/100 (weights re-normalized over present components)",
  "coverage": { "must_have": { "met": 10, "partial": 0, "missing": 0, "total": 10 }, … },
  "requirements": [
    { "kind": "must_have", "skill": "python", "status": "met",
      "reason": "Skill 'python' is present in the candidate's profile.",
      "evidence": [{ "snippet": "Led the migration … to Python and FastAPI",
                     "source": "skills", "match_type": "lexical" }] }
  ]
}
```

Statuses: `met · partial · missing · unknown · advisory` (advisory = soft
requirement, not scored). Evidence `match_type`: `lexical | computed | semantic`.

## Screening

| method | path | description |
|---|---|---|
| GET | `/screening` | applications that currently have a stored question set |
| GET | `/screening/applications/{application_id}` | stored questions |
| POST | `/screening/applications/{application_id}/generate` | generate (replaces the set), 201 |

## Tags

| method | path | description |
|---|---|---|
| GET | `/tags` | all tags with `usage_count` |

## Cookbook — verified `curl` examples

Every command below was executed verbatim against the Docker demo stack
(`docker compose up --build -d && docker compose exec api python -m app.seed`).
Outputs are trimmed; ids differ between stacks, so the snippets derive ids
into shell variables where needed.

### 1. Health

```bash
curl -s localhost:8000/api/v1/health | jq '{status, db: .database.dialect, ai: .ai.provider, counts}'
# { "status": "ok", "db": "postgresql", "ai": "mock",
#   "counts": { "candidates": 10, "jobs": 4, "open_jobs": 4, "applications": 10 } }
```

### 2. Create a job from a JD file

```bash
curl -s -X POST localhost:8000/api/v1/jobs/upload \
  -F "file=@examples/jobs/support-team-lead.md" \
  -F "title=Support Team Lead" -F "company=Lighthouse Cargo" -o job.json
jq '{id, title, requirements: (.requirements | length)}' job.json
# { "id": 5, "title": "Support Team Lead", "requirements": 10 }
JOB_ID=$(jq .id job.json)
```

### 3. Upload resumes (PDF/DOCX/TXT)

```bash
curl -s -X POST localhost:8000/api/v1/candidates/upload \
  -F "file=@examples/resumes/dana_whitfield.resume.txt" -o cand.json
jq '{id, full_name, years_experience, skills: (.skills | length)}' cand.json
# { "id": 11, "full_name": "Dana Whitfield", "years_experience": 6.7, "skills": 12 }
CAND_ID=$(jq .id cand.json)
```

### 4. List with pagination (limit/offset + total count)

```bash
curl -si "localhost:8000/api/v1/candidates?limit=2" | grep -iE '^HTTP|x-total-count'
# HTTP/1.1 200 OK
# x-total-count: 12
curl -s "localhost:8000/api/v1/candidates?limit=2&offset=2" | jq -r '.[].full_name'
```

### 5. Ranked matching for a job

```bash
curl -s "localhost:8000/api/v1/matching/job/$JOB_ID?limit=3" | jq -r \
  '.[] | "\(.candidate_name): \(.composite_score)/100"'
# Dana Whitfield: 71.9/100
# Sofia Petrova: 71.9/100
# Lucas Meyer: 57.8/100
```

### 6. Explain one pair (evidence + published formula)

```bash
curl -s "localhost:8000/api/v1/matching/pair?job_id=$JOB_ID&candidate_id=$CAND_ID" | jq '{composite_score, formula}'
# { "composite_score": 71.9,
#   "formula": "0.75·must_have[62%] + 0.12·experience[100%] + 0.12·domain[100%] = 71.9/100 (weights re-normalized over present components)" }
```

### 7. Pipeline: add → move → note

```bash
APP_ID=$(curl -s -X POST localhost:8000/api/v1/applications \
  -H 'Content-Type: application/json' \
  -d "{\"candidate_id\": $CAND_ID, \"job_id\": $JOB_ID}" | jq .id)

curl -s -X PATCH "localhost:8000/api/v1/applications/$APP_ID/stage" \
  -H 'Content-Type: application/json' \
  -d '{"to_stage": "SCREENING", "note": "Phone screen scheduled"}' | jq '{stage, events: (.stage_events | length)}'
# { "stage": "SCREENING", "events": 2 }

curl -s -X POST "localhost:8000/api/v1/candidates/$CAND_ID/notes" \
  -H 'Content-Type: application/json' \
  -d '{"body": "Strong SQL foundation, motivated transition.", "author": "Recruiter"}' | jq -r '.id'
```

### 8. Screening questions (grounded in the match)

```bash
curl -s -X POST "localhost:8000/api/v1/screening/applications/$APP_ID/generate" | jq -r \
  '.[0] | "\(.category): \(.question)\n    rationale: \(.rationale)"'
# technical: <question text written for this application's actual matches>
#     rationale: <one line quoting the match signal it checks>
```

### 9. Pipeline board

```bash
curl -s "localhost:8000/api/v1/applications/board?job_id=$JOB_ID" | jq 'map_values(length)'
# { "NEW": 0, "SCREENING": 1, "SHORTLISTED": 0, "INTERVIEW": 0, "OFFER": 0, "HIRED": 0, "REJECTED": 0 }
```

**Verify every example file in one go:** `scripts/verify_examples.sh` uploads
everything under `examples/` and prints an extraction summary.

## Conventions

* JSON everywhere except the two multipart uploads (≤ 10 MB).
* All list endpoints accept `limit`/`offset` (clamps: jobs/candidates 1–200,
  applications 1–500) and return the total matching count in the
  **`X-Total-Count`** response header (exposed to browsers via CORS).
  Ordering is newest-first unless noted.
* The API is unauthenticated in the demo — see SECURITY.md before exposing it.
