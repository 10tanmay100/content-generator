"""Health endpoint tests."""


def test_health_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_readiness_ok(client):
    resp = client.get("/api/v1/health/ready")
    assert resp.status_code == 200


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "service" in resp.json()
