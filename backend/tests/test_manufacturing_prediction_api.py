from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import create_app
from app.models.manufacturing_prediction import ManufacturingPredictionRun
from app.models.user import Base


@pytest.fixture()
def api_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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


def _headers_for(api_client: TestClient, suffix: str) -> dict[str, str]:
    api_client.post(
        "/api/v1/auth/register",
        json={
            "username": f"prediction_api_{suffix}",
            "email": f"prediction-api-{suffix}@example.com",
            "password": "Password123",
        },
    )
    login = api_client.post(
        "/api/v1/auth/login",
        json={"username": f"prediction_api_{suffix}", "password": "Password123"},
    )
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def _seed_history(api_client: TestClient, headers: dict[str, str]) -> None:
    for day, temperature, vibration, unit_energy, cement_output in (
        ("2026-08-01", 70, 3.1, 70, 80),
        ("2026-08-02", 75, 3.8, 75, 100),
        ("2026-08-03", 82, 5.2, 90, 120),
    ):
        assert api_client.post(
            "/api/v1/equipment-records",
            headers=headers,
            json={
                "date": day,
                "equipment_name": "水泥磨",
                "status": "检修" if day == "2026-08-03" else "运行",
                "running_hours": 22,
                "fault_count": 1 if day == "2026-08-03" else 0,
                "temperature": temperature,
                "vibration": vibration,
            },
        ).status_code == 201
        assert api_client.post(
            "/api/v1/energy-records",
            headers=headers,
            json={
                "date": day,
                "production_line": "1号线",
                "electricity_consumption": unit_energy,
                "coal_consumption": unit_energy + 30,
                "unit_energy_consumption": unit_energy,
            },
        ).status_code == 201
        assert api_client.post(
            "/api/v1/production-records",
            headers=headers,
            json={
                "date": day,
                "production_line": "1号线",
                "clinker_output": cement_output,
                "cement_output": cement_output,
                "planned_output": 100,
                "completion_rate": 0,
                "running_hours": 22,
                "downtime_hours": 2,
            },
        ).status_code == 201


def test_authenticated_user_can_create_and_persist_prediction(api_client: TestClient) -> None:
    headers = _headers_for(api_client, "owner")
    _seed_history(api_client, headers)

    response = api_client.post(
        "/api/v1/manufacturing-predictions",
        headers=headers,
        json={
            "prediction_types": ["equipment_risk"],
            "equipment_name": "水泥磨",
            "forecast_horizon_days": 7,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["id"] > 0
    assert body["data"]["prediction_result"]["equipment_predictions"]
    assert body["data"]["total"] == 1


def test_unauthenticated_user_cannot_access_prediction_api(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/manufacturing-predictions")

    assert response.status_code == 401


def test_user_can_list_paginated_own_predictions(api_client: TestClient) -> None:
    headers = _headers_for(api_client, "list")
    _seed_history(api_client, headers)
    for prediction_type in ("equipment_risk", "energy_consumption"):
        response = api_client.post(
            "/api/v1/manufacturing-predictions",
            headers=headers,
            json={"prediction_types": [prediction_type], "forecast_horizon_days": 7},
        )
        assert response.status_code == 201

    history = api_client.get(
        "/api/v1/manufacturing-predictions?page=2&page_size=1",
        headers=headers,
    )

    assert history.status_code == 200
    data = history.json()["data"]
    assert data["total"] == 2
    assert data["page"] == 2
    assert data["page_size"] == 1
    assert len(data["items"]) == 1


def test_creator_can_read_prediction_detail(api_client: TestClient) -> None:
    headers = _headers_for(api_client, "detail")
    _seed_history(api_client, headers)
    created = api_client.post(
        "/api/v1/manufacturing-predictions",
        headers=headers,
        json={"prediction_types": ["production_completion"], "production_line": "1号线"},
    ).json()["data"]

    detail = api_client.get(
        f"/api/v1/manufacturing-predictions/{created['id']}", headers=headers
    )

    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == created["id"]


def test_predictions_are_isolated_between_users(api_client: TestClient) -> None:
    owner_headers = _headers_for(api_client, "isolated-owner")
    other_headers = _headers_for(api_client, "isolated-other")
    _seed_history(api_client, owner_headers)
    created = api_client.post(
        "/api/v1/manufacturing-predictions",
        headers=owner_headers,
        json={"prediction_types": ["energy_consumption"]},
    ).json()["data"]

    response = api_client.get(
        f"/api/v1/manufacturing-predictions/{created['id']}", headers=other_headers
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"prediction_types": ["unsupported_type"]},
        {"prediction_types": ["equipment_risk"], "forecast_horizon_days": 0},
    ],
)
def test_prediction_api_validates_request_payload(
    api_client: TestClient, payload: dict
) -> None:
    headers = _headers_for(api_client, f"invalid-{len(str(payload))}")

    response = api_client.post(
        "/api/v1/manufacturing-predictions", headers=headers, json=payload
    )

    assert response.status_code == 422
