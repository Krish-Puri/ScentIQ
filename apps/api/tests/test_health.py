"""Tests for Health & Envelope Standards (EPIC-01).
"""
def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "healthy"
    assert "request_id" in data["meta"]
    assert response.headers.get("X-Request-ID") == data["meta"]["request_id"]


def test_readiness_check(client):
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["database"] == "connected"
    assert data["data"]["status"] == "ready"


def test_custom_request_id_propagated(client):
    custom_id = "test-custom-uuid-1234"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id
    assert response.json()["meta"]["request_id"] == custom_id
