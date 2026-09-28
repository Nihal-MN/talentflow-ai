"""Pipeline endpoints: applications, stage moves + audit trail, board, activity."""

from __future__ import annotations


def _add_to_pipeline(client, candidate_id: int, job_id: int) -> dict:
    response = client.post(
        "/api/v1/applications", json={"candidate_id": candidate_id, "job_id": job_id}
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_application_starts_at_new(client, fullstack_job, amira):
    application = _add_to_pipeline(client, amira["id"], fullstack_job["id"])
    assert application["stage"] == "NEW"
    assert application["candidate"]["full_name"] == "Amira Haddad"
    assert application["job"]["title"] == "Senior Full Stack Engineer"
    assert application["stage_events"][0]["from_stage"] is None
    assert application["stage_events"][0]["to_stage"] == "NEW"


def test_create_application_is_idempotent(client, fullstack_job, amira):
    first = _add_to_pipeline(client, amira["id"], fullstack_job["id"])
    second = _add_to_pipeline(client, amira["id"], fullstack_job["id"])
    assert first["id"] == second["id"]


def test_moving_through_the_pipeline_records_events(client, fullstack_job, amira):
    application = _add_to_pipeline(client, amira["id"], fullstack_job["id"])

    for stage in ("SCREENING", "SHORTLISTED"):
        response = client.patch(
            f"/api/v1/applications/{application['id']}/stage",
            json={"to_stage": stage, "note": f"Moving to {stage.title()}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["stage"] == stage

    events = client.get(f"/api/v1/applications/{application['id']}").json()["stage_events"]
    assert [(e["from_stage"], e["to_stage"]) for e in events] == [
        (None, "NEW"),
        ("NEW", "SCREENING"),
        ("SCREENING", "SHORTLISTED"),
    ]
    assert events[-1]["note"] == "Moving to Shortlisted"

    # Same-stage move is a no-op (no duplicate event).
    client.patch(
        f"/api/v1/applications/{application['id']}/stage", json={"to_stage": "SHORTLISTED"}
    )
    events = client.get(f"/api/v1/applications/{application['id']}").json()["stage_events"]
    assert len(events) == 3


def test_stage_move_rejects_unknown_stage(client, fullstack_job, amira):
    application = _add_to_pipeline(client, amira["id"], fullstack_job["id"])
    response = client.patch(
        f"/api/v1/applications/{application['id']}/stage", json={"to_stage": "CEO_APPROVED"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_board_groups_by_stage(client, fullstack_job, amira):
    application = _add_to_pipeline(client, amira["id"], fullstack_job["id"])
    client.patch(
        f"/api/v1/applications/{application['id']}/stage", json={"to_stage": "INTERVIEW"}
    )

    board = client.get("/api/v1/applications/board").json()
    assert set(board) == {
        "NEW", "SCREENING", "SHORTLISTED", "INTERVIEW", "OFFER", "HIRED", "REJECTED",
    }
    assert len(board["INTERVIEW"]) == 1
    assert board["INTERVIEW"][0]["candidate"]["full_name"] == "Amira Haddad"
    assert board["NEW"] == []


def test_activity_feed_returns_latest_first(client, fullstack_job, amira):
    application = _add_to_pipeline(client, amira["id"], fullstack_job["id"])
    client.patch(
        f"/api/v1/applications/{application['id']}/stage", json={"to_stage": "SCREENING"}
    )
    activity = client.get("/api/v1/applications/activity").json()
    assert len(activity) == 2
    assert activity[0]["to_stage"] == "SCREENING"
    assert activity[0]["candidate_name"] == "Amira Haddad"
    assert activity[1]["to_stage"] == "NEW"


def test_list_applications_filters(client, fullstack_job, amira):
    _add_to_pipeline(client, amira["id"], fullstack_job["id"])

    by_job = client.get("/api/v1/applications", params={"job_id": fullstack_job["id"]}).json()
    assert len(by_job) == 1

    by_candidate = client.get(
        "/api/v1/applications", params={"candidate_id": amira["id"]}
    ).json()
    assert len(by_candidate) == 1

    empty = client.get("/api/v1/applications", params={"stage": "HIRED"}).json()
    assert empty == []


def test_delete_application_removes_it(client, fullstack_job, amira):
    application = _add_to_pipeline(client, amira["id"], fullstack_job["id"])
    assert client.delete(f"/api/v1/applications/{application['id']}").status_code == 204
    assert client.get(f"/api/v1/applications/{application['id']}").status_code == 404


def test_application_validation_errors(client):
    response = client.post("/api/v1/applications", json={"candidate_id": 999, "job_id": 999})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
