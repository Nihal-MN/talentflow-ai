"""Candidate endpoints: resume ingestion, detail, notes, tags, errors."""

from __future__ import annotations

from tests.conftest import resume_path


def test_upload_resume_extracts_structured_profile(client):
    path = resume_path("amira_haddad.resume.pdf")
    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": (path.name, path.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    candidate = response.json()

    assert candidate["full_name"] == "Amira Haddad"
    assert candidate["email"] == "amira.haddad@example.com"
    assert candidate["location"] == "Dubai, UAE"
    assert candidate["extraction_method"] == "mock"
    assert candidate["years_experience"] and candidate["years_experience"] > 7

    titles = [e["title"] for e in candidate["experiences"]]
    assert any("Senior Software Engineer" in (t or "") for t in titles)
    current = [e for e in candidate["experiences"] if e["is_current"]]
    assert current and current[0]["end_date"] is None

    skills = {s["normalized_name"] for s in candidate["skills"]}
    assert {"python", "fastapi", "react", "typescript", "postgresql", "docker", "aws"} <= skills

    # Every skill records where it came from (evidence), when available.
    assert any(s["evidence"] for s in candidate["skills"])

    assert candidate["resume_filename"] == path.name
    # Raw text is kept as an evidence source.
    assert "Cedar Freight" in candidate["resume_text"]


def test_upload_docx_and_txt_formats(client):
    for filename in ("daniel_okafor.resume.docx", "priya_nair.resume.txt"):
        path = resume_path(filename)
        response = client.post(
            "/api/v1/candidates/upload",
            files={"file": (path.name, path.read_bytes(), "application/octet-stream")},
        )
        assert response.status_code == 201, response.text
        assert response.json()["full_name"]


def test_upload_rejects_unsupported_file_type(client):
    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": ("photo.jpg", b"\xff\xd8\xff", "image/jpeg")},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "ingestion_error"
    assert "Unsupported file type" in body["error"]["message"]


def test_upload_rejects_empty_and_textless_files(client):
    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ingestion_error"

    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": ("noise.txt", b"xxxxxxxxxx", "text/plain")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ingestion_error"


def test_list_candidates_filters(client, amira):
    everything = client.get("/api/v1/candidates").json()
    assert len(everything) == 1
    assert everything[0]["skills"]

    by_query = client.get("/api/v1/candidates", params={"q": "Amira"}).json()
    assert len(by_query) == 1

    by_skill = client.get("/api/v1/candidates", params={"skill": "fastapi"}).json()
    assert len(by_skill) == 1

    no_match = client.get("/api/v1/candidates", params={"skill": "cobol"}).json()
    assert no_match == []


def test_candidate_detail_and_delete(client, amira):
    detail = client.get(f"/api/v1/candidates/{amira['id']}").json()
    assert detail["id"] == amira["id"]

    assert client.delete(f"/api/v1/candidates/{amira['id']}").status_code == 204
    assert client.get(f"/api/v1/candidates/{amira['id']}").status_code == 404


def test_notes_lifecycle(client, amira):
    candidate_id = amira["id"]
    response = client.post(
        f"/api/v1/candidates/{candidate_id}/notes",
        json={"body": "Great logistics background.", "author": "Nihal"},
    )
    assert response.status_code == 201
    note = response.json()
    assert note["author"] == "Nihal"

    detail = client.get(f"/api/v1/candidates/{candidate_id}").json()
    assert [n["id"] for n in detail["notes"]] == [note["id"]]

    assert client.delete(f"/api/v1/candidates/{candidate_id}/notes/{note['id']}").status_code == 204
    assert client.get(f"/api/v1/candidates/{candidate_id}").json()["notes"] == []


def test_note_validation_errors(client, amira):
    response = client.post(f"/api/v1/candidates/{amira['id']}/notes", json={"body": ""})
    assert response.status_code == 422

    response = client.post("/api/v1/candidates/9999/notes", json={"body": "hi"})
    assert response.status_code == 404


def test_tags_are_created_reused_and_detached(client, amira):
    candidate_id = amira["id"]
    response = client.post(
        f"/api/v1/candidates/{candidate_id}/tags", json={"name": "Top-Match", "color": "emerald"}
    )
    assert response.status_code == 201
    tag = response.json()
    assert tag["name"] == "top-match"  # normalized to lowercase

    # Re-adding the same tag is idempotent (same tag row).
    again = client.post(f"/api/v1/candidates/{candidate_id}/tags", json={"name": "top-match"})
    assert again.json()["id"] == tag["id"]

    usage = client.get("/api/v1/tags").json()
    assert usage[0]["name"] == "top-match"
    assert usage[0]["usage_count"] == 1

    assert client.delete(f"/api/v1/candidates/{candidate_id}/tags/{tag['id']}").status_code == 204
    assert (
        client.get(f"/api/v1/candidates/{candidate_id}").json()
        == client.get(f"/api/v1/candidates/{candidate_id}").json()
    )  # stable read after detach
    assert client.get("/api/v1/tags").json()[0]["usage_count"] == 0

    # Removing a tag that is not attached -> 404
    response = client.delete(f"/api/v1/candidates/{candidate_id}/tags/{tag['id']}")
    assert response.status_code == 404
