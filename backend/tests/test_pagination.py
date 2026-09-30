"""Pagination: limit/offset on collections and the X-Total-Count header."""

from __future__ import annotations

from app.seed.demo_jobs import DEMO_JOBS
from tests.conftest import resume_path

JD = DEMO_JOBS["senior-full-stack-engineer"]["text"]


def _create_job(client, title):
    response = client.post("/api/v1/jobs", json={"title": title, "jd_text": JD})
    assert response.status_code == 201
    return response.json()


def test_jobs_limit_offset_and_total_count(client):
    for i in range(3):
        _create_job(client, f"Job {i}")
    first = client.get("/api/v1/jobs", params={"limit": 2})
    assert first.status_code == 200
    assert first.headers["x-total-count"] == "3"
    assert len(first.json()) == 2
    second = client.get("/api/v1/jobs", params={"limit": 2, "offset": 2})
    assert len(second.json()) == 1
    past_end = client.get("/api/v1/jobs", params={"offset": 99})
    assert past_end.json() == []
    assert past_end.headers["x-total-count"] == "3"


def test_jobs_filtered_count_reflects_filters(client):
    _create_job(client, "Unique Support Lead")
    _create_job(client, "Other Role")
    only = client.get("/api/v1/jobs", params={"q": "Unique Support"})
    assert only.headers["x-total-count"] == "1"
    assert len(only.json()) == 1


def test_candidates_limit_offset_and_total_count(client):
    for filename in (
        "amira_haddad.resume.pdf",
        "daniel_okafor.resume.docx",
        "marco_rossi.resume.txt",
    ):
        with resume_path(filename).open("rb") as fh:
            response = client.post(
                "/api/v1/candidates/upload",
                files={"file": (filename, fh, "application/octet-stream")},
            )
        assert response.status_code == 201
    listed = client.get("/api/v1/candidates", params={"limit": 2})
    assert listed.headers["x-total-count"] == "3"
    assert len(listed.json()) == 2
    page_two = client.get("/api/v1/candidates", params={"limit": 2, "offset": 2})
    assert len(page_two.json()) == 1


def test_applications_offset_and_total_count(client, amira, fullstack_job):
    created = client.post(
        "/api/v1/applications",
        json={"candidate_id": amira["id"], "job_id": fullstack_job["id"]},
    )
    assert created.status_code == 201
    listed = client.get("/api/v1/applications")
    assert listed.headers["x-total-count"] == "1"
    assert len(listed.json()) == 1
    past_end = client.get("/api/v1/applications", params={"offset": 5})
    assert past_end.json() == []
    assert past_end.headers["x-total-count"] == "1"


def test_invalid_pagination_params_are_422(client):
    assert client.get("/api/v1/jobs", params={"limit": "lots"}).status_code == 422
    assert client.get("/api/v1/candidates", params={"offset": "x"}).status_code == 422
