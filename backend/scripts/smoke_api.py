"""Quick end-to-end smoke test (dev tool).

Runs the full backend flow in-process against a throwaway SQLite database:

    cd backend && uv run python scripts/smoke_api.py

Not part of the pytest suite — this is a fast human-readable sanity check.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/smoke_api.db")

from starlette.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401  (register tables)
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402

JD_TEXT = """Senior Full Stack Engineer

We are building the logistics platform of the future and need a Senior Full Stack Engineer.

Requirements:
- 5+ years of software engineering experience
- Expert-level Python and FastAPI
- Strong React and TypeScript skills
- PostgreSQL and Docker experience
- Experience with AWS
- Bachelor's degree in Computer Science or related field

Nice to have:
- Kubernetes
- Experience in logistics or supply chain

Location: Dubai, UAE
"""

RESUME_TEXT = """Amira Haddad
Senior Software Engineer - Dubai, UAE
amira.haddad@example.com | +971 50 555 0101 | linkedin.com/in/amirahaddad

Summary
Senior full-stack engineer with 8 years of experience building logistics and fintech products.

Experience
Senior Software Engineer - Cedar Freight (Dubai, UAE)
Mar 2021 - Present
- Led the migration of the shipment tracking platform to Python and FastAPI
- Built React and TypeScript dashboards used by 300+ operations staff
- Designed PostgreSQL schemas and pgvector-based document search
- Deployed services on AWS with Docker and GitHub Actions

Software Engineer - Dune Analytics Ltd (Remote)
Jun 2018 - Feb 2021
- Developed REST APIs in Django and Flask
- Worked with MongoDB and Redis caching layers

Education
BSc in Computer Science - American University of Sharjah, 2018

Skills
Python, FastAPI, React, TypeScript, PostgreSQL, Docker, AWS, GitHub Actions, SQL
"""


def main() -> int:
    Base.metadata.create_all(engine)
    client = TestClient(app)

    r = client.get("/api/v1/health/live")
    assert r.status_code == 200, r.text
    print("health/live  ✓", r.json())

    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json()["database"]["status"] == "ok", r.text
    print("health       ✓", r.json()["status"], "| db:", r.json()["database"]["dialect"])

    r = client.post(
        "/api/v1/jobs",
        json={"title": "Senior Full Stack Engineer", "jd_text": JD_TEXT},
    )
    assert r.status_code == 201, r.text
    job = r.json()
    print(
        f"job create   ✓ id={job['id']} must={job['must_have_count']} "
        f"preferred={job['preferred_count']}"
    )

    r = client.post(
        "/api/v1/candidates/upload",
        files={"file": ("amira_haddad.txt", RESUME_TEXT.encode(), "text/plain")},
    )
    assert r.status_code == 201, r.text
    candidate = r.json()
    print(
        f"resume       ✓ {candidate['full_name']} | skills={len(candidate['skills'])} "
        f"| roles={len(candidate['experiences'])} | years={candidate['years_experience']}"
    )

    r = client.get(f"/api/v1/matching/job/{job['id']}")
    assert r.status_code == 200, r.text
    ranked = r.json()
    for result in ranked:
        print(
            f"match        ✓ {result['candidate_name']} → {result['composite_score']}/100 "
            f"| formula: {result['formula'][:70]}..."
        )
        statuses = [req["status"] for req in result["requirements"]]
        print(
            "               statuses:",
            {s: statuses.count(s) for s in sorted(set(statuses))},
        )

    candidate_id = candidate["id"]
    r = client.post(
        "/api/v1/applications", json={"candidate_id": candidate_id, "job_id": job["id"]}
    )
    assert r.status_code == 201, r.text
    application = r.json()
    print(f"application  ✓ id={application['id']} stage={application['stage']}")

    r = client.patch(
        f"/api/v1/applications/{application['id']}/stage",
        json={"to_stage": "SCREENING", "note": "Strong profile — moving to screening"},
    )
    assert r.status_code == 200 and r.json()["stage"] == "SCREENING", r.text
    print("stage move   ✓ NEW → SCREENING")

    r = client.post(
        f"/api/v1/candidates/{candidate_id}/notes",
        json={"body": "Excellent logistics background, verify AWS depth on the call."},
    )
    assert r.status_code == 201, r.text
    print("note         ✓", r.json()["id"])

    r = client.post(f"/api/v1/screening/applications/{application['id']}/generate")
    assert r.status_code == 201, r.text
    print(f"screening    ✓ {len(r.json())} questions generated")

    r = client.get("/api/v1/health")
    counts = r.json()["counts"]
    print("counts       ✓", counts)
    assert counts["jobs"] >= 1 and counts["candidates"] >= 1 and counts["applications"] >= 1

    print("\nSMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
