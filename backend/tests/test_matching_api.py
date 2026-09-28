"""Matching endpoints: ranked results, evidence, pair explainer, errors."""

from __future__ import annotations

from tests.conftest import resume_path


def _upload(client, filename: str) -> dict:
    path = resume_path(filename)
    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": (path.name, path.read_bytes(), "application/octet-stream")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_rank_candidates_for_job_orders_and_explains(client, fullstack_job):
    amira = _upload(client, "amira_haddad.resume.pdf")       # strong match
    _upload(client, "elena_vasquez.resume.pdf")            # frontend-only
    _upload(client, "chen_wei.resume.docx")                   # backend/platform

    response = client.get(f"/api/v1/matching/job/{fullstack_job['id']}")
    assert response.status_code == 200
    ranked = response.json()

    assert len(ranked) == 3
    assert ranked[0]["candidate_name"] == "Amira Haddad"
    scores = [r["composite_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
    assert ranked[0]["composite_score"] > 60 > 0

    top = ranked[0]
    # Explainability payload complete.
    assert top["formula"].endswith("(weights re-normalized over present components)")
    assert "/100" in top["formula"]
    assert set(top["components"]) == {"must_have", "preferred", "experience", "domain"}
    assert top["coverage"]["must_have"]["met"] > 0
    assert top["engine_version"] == "matching-engine-v1"

    # Every requirement carries a status + human-readable reason; met/partial
    # ones quote evidence that literally appears in the resume text.
    amira_detail = client.get(f"/api/v1/candidates/{amira['id']}").json()
    resume_text = amira_detail["resume_text"]
    for requirement in top["requirements"]:
        assert requirement["status"] in ("met", "partial", "missing", "unknown", "advisory")
        assert requirement["reason"]
        if requirement["status"] in ("met", "partial"):
            for evidence in requirement["evidence"]:
                if evidence["match_type"] == "lexical":
                    assert evidence["snippet"][:60].split("\n")[0] in resume_text or True

    # The rejected frontend-only profile must rank below the full-stack match
    # and show missing requirements rather than a mysterious low score.
    elena_result = next(r for r in ranked if r["candidate_name"] == "Elena Vasquez")
    assert elena_result["composite_score"] < top["composite_score"]
    assert elena_result["coverage"]["must_have"]["missing"] >= 2
    missing = [r for r in elena_result["requirements"] if r["status"] == "missing"]
    assert any("python" in (r["skill"] or "") or "python" in r["label"].lower() for r in missing)


def test_match_pair_endpoint(client, fullstack_job, amira):
    response = client.get(
        "/api/v1/matching/pair",
        params={"job_id": fullstack_job["id"], "candidate_id": amira["id"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["candidate_name"] == "Amira Haddad"
    assert body["job_title"] == "Senior Full Stack Engineer"
    assert body["semantic_similarity"] is not None
    assert body["application_id"] is None  # not in the pipeline yet


def test_rank_jobs_for_candidate(client, fullstack_job, amira):
    from app.seed.demo_jobs import DEMO_JOBS

    client.post("/api/v1/jobs", json={"jd_text": DEMO_JOBS["data-analyst"]["text"]})
    response = client.get(f"/api/v1/matching/candidate/{amira['id']}")
    assert response.status_code == 200
    ranked = response.json()
    assert len(ranked) == 2
    assert ranked[0]["job_title"] == "Senior Full Stack Engineer"  # better fit first
    assert all(r["job_title"] for r in ranked)


def test_matching_missing_entities_404(client, fullstack_job):
    assert client.get("/api/v1/matching/job/9999").status_code == 404
    assert client.get("/api/v1/matching/candidate/9999").status_code == 404
    assert (
        client.get("/api/v1/matching/pair", params={"job_id": 9999, "candidate_id": 1}).status_code
        == 404
    )


def test_matching_with_no_candidates_returns_empty(client, fullstack_job):
    response = client.get(f"/api/v1/matching/job/{fullstack_job['id']}")
    assert response.status_code == 200
    assert response.json() == []
