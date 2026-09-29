"""Job endpoints: creation (paste + upload), extraction quality, CRUD, errors."""

from __future__ import annotations

from app.seed.demo_jobs import DEMO_JOBS

FULLSTACK_JD = DEMO_JOBS["senior-full-stack-engineer"]["text"]


def test_create_job_extracts_structured_requirements(client):
    response = client.post(
        "/api/v1/jobs",
        json={
            "title": "Senior Full Stack Engineer",
            "company": "Cedar Freight",
            "jd_text": FULLSTACK_JD,
        },
    )
    assert response.status_code == 201
    job = response.json()

    assert job["title"] == "Senior Full Stack Engineer"
    assert job["company"] == "Cedar Freight"
    assert job["status"] == "open"
    assert job["extraction_method"] == "mock"
    assert job["seniority"] == "senior"
    assert job["domain"] == "logistics"
    assert job["location"] == "Dubai"

    must = [r for r in job["requirements"] if r["kind"] == "must_have"]
    preferred = [r for r in job["requirements"] if r["kind"] == "preferred"]
    assert len(must) >= 8
    assert len(preferred) >= 2

    skills = {r["normalized_skill"] for r in must if r["category"] == "skill"}
    assert {"python", "fastapi", "react", "typescript", "postgresql", "docker", "aws"} <= skills

    years = [r for r in must if r["category"] == "experience"]
    assert years and years[0]["min_years"] == 5.0

    education = [r for r in must if r["category"] == "education"]
    assert education, "expected a degree requirement"

    # Preferred section must not leak into must-haves.
    assert any(r["normalized_skill"] == "kubernetes" for r in preferred)
    assert not any(r["normalized_skill"] == "kubernetes" for r in must)


def test_create_job_missing_title_is_inferred_from_text(client):
    response = client.post("/api/v1/jobs", json={"jd_text": FULLSTACK_JD})
    assert response.status_code == 201
    assert "Full Stack Engineer" in response.json()["title"]


def test_create_job_rejects_short_description(client):
    response = client.post("/api/v1/jobs", json={"jd_text": "too short"})
    # Pydantic min_length=30 rejects it at the schema layer.
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_job_from_txt_upload(client):
    response = client.post(
        "/api/v1/jobs/upload",
        files={"file": ("jd.txt", FULLSTACK_JD.encode(), "text/plain")},
        data={"company": "Cedar Freight"},
    )
    assert response.status_code == 201
    job = response.json()
    assert job["source"] == "upload"
    assert job["must_have_count"] >= 8


def test_list_and_filter_jobs(client, fullstack_job):
    client.post("/api/v1/jobs", json={"jd_text": DEMO_JOBS["data-analyst"]["text"]})

    everything = client.get("/api/v1/jobs").json()
    assert len(everything) == 2

    filtered = client.get("/api/v1/jobs", params={"q": "Data"}).json()
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Data Analyst"

    by_status = client.get("/api/v1/jobs", params={"status": "open"}).json()
    assert len(by_status) == 2


def test_job_detail_roundtrip(client, fullstack_job):
    response = client.get(f"/api/v1/jobs/{fullstack_job['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == fullstack_job["id"]
    assert len(body["requirements"]) == len(fullstack_job["requirements"])
    assert body["description_text"].startswith("Senior Full Stack Engineer")


def test_update_job_status(client, fullstack_job):
    response = client.patch(f"/api/v1/jobs/{fullstack_job['id']}", json={"status": "closed"})
    assert response.status_code == 200
    assert response.json()["status"] == "closed"

    # Invalid status is rejected with a structured error.
    response = client.patch(f"/api/v1/jobs/{fullstack_job['id']}", json={"status": "banana"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_delete_job(client, fullstack_job):
    assert client.delete(f"/api/v1/jobs/{fullstack_job['id']}").status_code == 204
    assert client.get(f"/api/v1/jobs/{fullstack_job['id']}").status_code == 404


def test_missing_job_returns_structured_404(client):
    response = client.get("/api/v1/jobs/9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert "9999" in response.json()["error"]["message"]
