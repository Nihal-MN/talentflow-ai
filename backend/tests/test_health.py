"""Health endpoint tests."""

from __future__ import annotations


def test_liveness(client):
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_full_health_reports_dependencies_without_secrets(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["database"]["status"] == "ok"
    assert body["database"]["dialect"] == "sqlite"
    assert body["database"]["latency_ms"] is not None

    ai = body["ai"]
    assert ai["provider"] == "mock"
    assert ai["mode"] == "mock"
    assert ai["api_key_configured"] is False
    # No secret material of any kind is present in the payload.
    serialized = str(body).lower()
    assert "sk-" not in serialized
    assert "api_key" in serialized  # the *flag* is fine; the value is not

    assert set(body["counts"]) == {"candidates", "jobs", "open_jobs", "applications"}


def test_health_counts_reflect_created_data(client, fullstack_job, amira):
    body = client.get("/api/v1/health").json()["counts"]
    assert body["jobs"] == 1
    assert body["open_jobs"] == 1
    assert body["candidates"] == 1
    assert body["applications"] == 0


def test_unknown_route_uses_structured_error_shape(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
