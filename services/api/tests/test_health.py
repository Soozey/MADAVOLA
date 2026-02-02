def test_health_ready(client):
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    ready = client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
