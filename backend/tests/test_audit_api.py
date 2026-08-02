from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import create_app
from app.models.user import Base
from app.models.user import User


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
    app.state.testing_session = testing_session
    with TestClient(app) as test_client:
        yield test_client


def test_audit_logs_require_admin(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"username": "audit_user", "email": "audit@example.com", "password": "Password123"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "audit_user", "password": "Password123"},
    )

    response = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {login.json()['data']['access_token']}"},
    )

    assert response.status_code == 403


def test_admin_can_read_paginated_real_operation_logs(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"username": "audit_admin", "email": "audit_admin@example.com", "password": "Password123"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "audit_admin", "password": "Password123"},
    )
    token = login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with client.app.state.testing_session() as db:
        user = db.scalar(select(User).where(User.username == "audit_admin"))
        assert user is not None
        user.role = "ADMIN"
        db.commit()

    upload = client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": ("sales.csv", b"region,sales\nEast,120\n", "text/csv")},
    )
    assert upload.status_code == 201

    response = client.get("/api/v1/audit-logs?page=1&page_size=1", headers=headers)

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["pagination"] == {"page": 1, "page_size": 1, "total": 1, "total_pages": 1}
    assert len(payload["items"]) == 1
    assert payload["items"][0]["action"] == "DATASET_UPLOAD"
    assert payload["items"][0]["target_type"] == "dataset"
