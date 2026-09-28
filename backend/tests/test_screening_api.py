"""Screening-question endpoints: generation, persistence, regeneration."""

from __future__ import annotations

from tests.conftest import resume_path

VALID_CATEGORIES = {"technical", "experience", "gap_probe", "behavioral"}


def _pipeline(client, candidate_id: int, job_id: int) -> dict:
    response = client.post(
        "/api/v1/applications", json={"candidate_id": candidate_id, "job_id": job_id}
    )
    assert response.status_code == 201, response.text
    return response.json()


def _upload(client, filename: str) -> dict:
    path = resume_path(filename)
    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": (path.name, path.read_bytes(), "application/octet-stream")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_generate_questions_for_application(client, fullstack_job, amira):
    application = _pipeline(client, amira["id"], fullstack_job["id"])

    response = client.post(f"/api/v1/screening/applications/{application['id']}/generate")
    assert response.status_code == 201
    questions = response.json()

    assert 3 <= len(questions) <= 7
    categories = {q["category"] for q in questions}
    assert categories <= VALID_CATEGORIES
    assert "technical" in categories  # grounded in her matched skills
    assert "behavioral" in categories
    assert all(q["source"] == "mock" for q in questions)
    assert all(q["rationale"] for q in questions)
    assert all(q["question"].strip().endswith("?") for q in questions)


def test_gap_probes_appear_for_missing_must_haves(client, fullstack_job):
    # Elena is a frontend-only profile: several full-stack must-haves are missing.
    elena = _upload(client, "elena_vasquez.resume.pdf")
    application = _pipeline(client, elena["id"], fullstack_job["id"])

    questions = client.post(
        f"/api/v1/screening/applications/{application['id']}/generate"
    ).json()
    gap_probes = [q for q in questions if q["category"] == "gap_probe"]
    assert gap_probes, "expected gap probes for missing must-have skills"
    assert any("ramp" in q["question"].lower() or "come up to speed" in q["question"].lower() for q in gap_probes)


def test_questions_persist_and_regenerate_replaces_set(client, fullstack_job, amira):
    application = _pipeline(client, amira["id"], fullstack_job["id"])
    first = client.post(
        f"/api/v1/screening/applications/{application['id']}/generate"
    ).json()

    stored = client.get(f"/api/v1/screening/applications/{application['id']}").json()
    assert [q["id"] for q in stored] == [q["id"] for q in first]

    second = client.post(
        f"/api/v1/screening/applications/{application['id']}/generate"
    ).json()
    assert len(second) == len(first)

    # Regeneration replaces the set rather than appending to it.
    stored_after = client.get(f"/api/v1/screening/applications/{application['id']}").json()
    assert len(stored_after) == len(second)
    assert [q["question"] for q in stored_after] == [q["question"] for q in second]


def test_screening_page_lists_sets_with_counts(client, fullstack_job, amira):
    application = _pipeline(client, amira["id"], fullstack_job["id"])
    client.post(f"/api/v1/screening/applications/{application['id']}/generate")

    listing = client.get("/api/v1/screening").json()
    assert len(listing) == 1
    item = listing[0]
    assert item["candidate_name"] == "Amira Haddad"
    assert item["job_title"] == "Senior Full Stack Engineer"
    assert item["question_count"] >= 3
    assert item["source"] == "mock"


def test_screening_404s(client):
    assert client.get("/api/v1/screening/applications/9999").status_code == 404
    assert client.post("/api/v1/screening/applications/9999/generate").status_code == 404
