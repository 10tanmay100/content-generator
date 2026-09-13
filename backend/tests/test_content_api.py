"""Content generation endpoint tests (crew execution is mocked)."""
from unittest.mock import patch


def test_generate_requires_auth(client):
    resp = client.post("/api/v1/content/generate", json={"topic": "AI in healthcare"})
    assert resp.status_code == 401


def test_generate_rejects_short_topic(client, auth_headers):
    resp = client.post("/api/v1/content/generate", json={"topic": "AI"}, headers=auth_headers)
    assert resp.status_code == 422


@patch("app.services.cosmos_service.cosmos_service.upsert_job", return_value={})
def test_generate_accepts_valid_request(mock_upsert, client, auth_headers):
    payload = {
        "topic": "The future of renewable energy",
        "content_format": "blog",
        "tone": "professional",
        "target_audience": "sustainability enthusiasts",
        "word_count": 800,
    }
    resp = client.post("/api/v1/content/generate", json=payload, headers=auth_headers)
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "pending"
    assert "job_id" in body


def test_get_job_not_found(client, auth_headers):
    with patch("app.services.cosmos_service.cosmos_service.get_job", return_value=None):
        resp = client.get("/api/v1/jobs/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404
