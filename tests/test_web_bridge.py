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


def test_tools_call_unknown_tool():
    client = TestClient(web_app)
    r = client.post("/api/tools/call", json={"tool": "nope_nonexistent", "params": {}})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert "not directly runnable" in body["error"]


def test_tools_call_non_dict_params():
    client = TestClient(web_app)
    r = client.post("/api/tools/call", json={"tool": "manage_system", "params": [1, 2]})
    assert r.status_code == 200
    assert r.json()["success"] is False


def test_tools_call_system_status_shape():
    # Works with or without a live engine: always a JSON dict with success key.
    client = TestClient(web_app)
    r = client.post("/api/tools/call", json={"tool": "manage_system", "params": {}})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
    assert "success" in r.json()


def test_tools_call_bad_kwarg():
    client = TestClient(web_app)
    r = client.post(
        "/api/tools/call",
        json={"tool": "manage_containers", "params": {"operation": "list", "bogus_param": 1}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
