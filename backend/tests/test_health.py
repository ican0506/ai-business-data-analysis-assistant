def test_health_endpoint_returns_unified_response(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.health.is_database_available", lambda: True)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok", "database": "available"},
    }
