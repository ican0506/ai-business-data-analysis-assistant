def test_health_endpoint_returns_unified_response(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.health.is_database_available", lambda: True)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok", "database": "available"},
    }


def test_root_serves_frontend_entry(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "AI 智能数据分析助手" in response.text


def test_health_endpoint_allows_frontend_origin(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"
