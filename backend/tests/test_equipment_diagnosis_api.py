from collections.abc import Generator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import create_app
from app.models.user import Base


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app = create_app(create_tables=False)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


def _headers_for(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"username": "diagnosis_user", "email": "diagnosis@example.com", "password": "Password123"},
    )
    login = client.post("/api/v1/auth/login", json={"username": "diagnosis_user", "password": "Password123"})
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def test_equipment_diagnosis_returns_rule_based_high_risk_when_llm_is_unavailable(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.equipment_diagnosis_service.get_settings",
        lambda: SimpleNamespace(llm_provider="", llm_api_key=""),
    )
    headers = _headers_for(client)
    created = client.post(
        "/api/v1/equipment-records",
        headers=headers,
        json={
            "date": "2026-08-02",
            "equipment_name": "水泥磨",
            "status": "停机",
            "running_hours": 2,
            "fault_count": 2,
            "temperature": 84,
            "vibration": 5.4,
        },
    )
    assert created.status_code == 201

    response = client.post("/api/v1/equipment-diagnosis/%E6%B0%B4%E6%B3%A5%E7%A3%A8", headers=headers)

    assert response.status_code == 200
    diagnosis = response.json()["data"]
    assert diagnosis["equipment_name"] == "水泥磨"
    assert diagnosis["risk_level"] == "高风险"
    assert "温度异常升高" in diagnosis["problem_analysis"]
    assert "检查润滑系统" in diagnosis["suggestions"]
    assert diagnosis["mode"] == "rule_based"


def test_equipment_diagnosis_returns_404_for_unknown_equipment(client: TestClient) -> None:
    headers = _headers_for(client)

    response = client.post("/api/v1/equipment-diagnosis/%E4%B8%8D%E5%AD%98%E5%9C%A8", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "设备不存在"
