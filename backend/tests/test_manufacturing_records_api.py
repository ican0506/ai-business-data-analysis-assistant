from collections.abc import Generator
from pathlib import Path

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
        json={
            "username": "manufacturing_user",
            "email": "manufacturing@example.com",
            "password": "Password123",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "manufacturing_user", "password": "Password123"},
    )
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def test_manufacturing_record_apis_create_list_and_read_details(client: TestClient) -> None:
    headers = _headers_for(client)

    production = client.post(
        "/api/v1/production-records",
        headers=headers,
        json={
            "date": "2026-08-01",
            "production_line": "1号线",
            "clinker_output": 5000,
            "cement_output": 6500,
            "planned_output": 7000,
            "completion_rate": 92.86,
            "running_hours": 22.5,
            "downtime_hours": 1.5,
        },
    )
    equipment = client.post(
        "/api/v1/equipment-records",
        headers=headers,
        json={
            "date": "2026-08-01",
            "equipment_name": "水泥磨",
            "status": "运行",
            "running_hours": 22.5,
            "fault_count": 0,
            "temperature": 65,
            "vibration": 3.2,
        },
    )
    energy = client.post(
        "/api/v1/energy-records",
        headers=headers,
        json={
            "date": "2026-08-01",
            "production_line": "1号线",
            "electricity_consumption": 75,
            "coal_consumption": 105,
            "unit_energy_consumption": 98.5,
        },
    )

    assert production.status_code == 201
    assert equipment.status_code == 201
    assert energy.status_code == 201
    assert production.json()["data"]["production_line"] == "1号线"
    assert equipment.json()["data"]["equipment_name"] == "水泥磨"
    assert energy.json()["data"]["electricity_consumption"] == 75

    for endpoint, created in (
        ("production-records", production),
        ("equipment-records", equipment),
        ("energy-records", energy),
    ):
        listing = client.get(f"/api/v1/{endpoint}", headers=headers)
        detail = client.get(f"/api/v1/{endpoint}/{created.json()['data']['id']}", headers=headers)
        assert listing.status_code == 200
        assert listing.json()["data"]["total"] == 1
        assert detail.status_code == 200
        assert detail.json()["data"]["id"] == created.json()["data"]["id"]


def test_manufacturing_record_apis_require_login(client: TestClient) -> None:
    response = client.get("/api/v1/production-records")

    assert response.status_code == 401


def test_production_record_rejects_negative_hours(client: TestClient) -> None:
    headers = _headers_for(client)

    response = client.post(
        "/api/v1/production-records",
        headers=headers,
        json={
            "date": "2026-08-01",
            "production_line": "1号线",
            "clinker_output": 5000,
            "cement_output": 6500,
            "planned_output": 7000,
            "completion_rate": 92.86,
            "running_hours": -1,
            "downtime_hours": 1.5,
        },
    )

    assert response.status_code == 422


def test_manufacturing_migration_declares_all_three_tables() -> None:
    migration = (
        Path(__file__).resolve().parents[1]
        / "sql"
        / "006_create_manufacturing_records.sql"
    )

    content = migration.read_text(encoding="utf-8").lower()
    assert "create table if not exists production_records" in content
    assert "create table if not exists equipment_records" in content
    assert "create table if not exists energy_records" in content
