"""Smoke tests for FastAPI web bridge (fleet /logs + health)."""

from fastapi.testclient import TestClient

from server import web_app


def test_health():
    client = TestClient(web_app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["service"] == "podman-mcp"


def test_logs_endpoints():
    client = TestClient(web_app)
    r = client.get("/api/logs", params={"limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert "entries" in body
    assert "total" in body

    stats = client.get("/api/logs/stats")
    assert stats.status_code == 200
    assert "max_entries" in stats.json()
