from collections.abc import Generator

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
        json={"username": "equipment_manager", "email": "equipment@example.com", "password": "Password123"},
    )
    login = client.post("/api/v1/auth/login", json={"username": "equipment_manager", "password": "Password123"})
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def _create_equipment_record(client: TestClient, headers: dict[str, str], **overrides: object) -> None:
    payload = {
        "date": "2026-08-01",
        "equipment_name": "水泥磨",
        "status": "运行",
        "running_hours": 22.5,
        "fault_count": 0,
        "temperature": 65,
        "vibration": 3.2,
    }
    payload.update(overrides)
    response = client.post("/api/v1/equipment-records", headers=headers, json=payload)
    assert response.status_code == 201


def test_equipment_management_returns_only_the_latest_snapshot_per_equipment(client: TestClient) -> None:
    headers = _headers_for(client)
    _create_equipment_record(client, headers, date="2026-08-01", equipment_name="水泥磨", temperature=65)
    _create_equipment_record(client, headers, date="2026-08-02", equipment_name="水泥磨", temperature=83)
    _create_equipment_record(client, headers, date="2026-08-01", equipment_name="回转窑", temperature=72)

    response = client.get("/api/v1/equipment-management", headers=headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["equipment_name"] for item in items] == ["回转窑", "水泥磨"]
    assert items[1]["temperature"] == 83.0


def test_equipment_management_returns_ordered_history_and_latest_detail(client: TestClient) -> None:
    headers = _headers_for(client)
    _create_equipment_record(client, headers, date="2026-08-02", temperature=83, vibration=5.4)
    _create_equipment_record(client, headers, date="2026-08-01", temperature=65, vibration=3.2)

    detail = client.get("/api/v1/equipment-management/%E6%B0%B4%E6%B3%A5%E7%A3%A8", headers=headers)
    history = client.get("/api/v1/equipment-management/%E6%B0%B4%E6%B3%A5%E7%A3%A8/history", headers=headers)

    assert detail.status_code == 200
    assert detail.json()["data"]["temperature"] == 83.0
    assert history.status_code == 200
    assert [item["date"] for item in history.json()["data"]["items"]] == ["2026-08-01", "2026-08-02"]


def test_equipment_management_anomaly_rules_report_fault_status_temperature_and_vibration(client: TestClient) -> None:
    headers = _headers_for(client)
    _create_equipment_record(
        client,
        headers,
        date="2026-08-02",
        status="停机",
        fault_count=2,
        temperature=80,
        vibration=5.0,
    )

    response = client.get("/api/v1/equipment-management/anomalies", headers=headers)

    assert response.status_code == 200
    alerts = response.json()["data"]["items"]
    assert {item["rule_id"] for item in alerts} == {"fault_count", "status", "temperature", "vibration"}
    assert all(item["equipment_name"] == "水泥磨" for item in alerts)
