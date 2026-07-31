from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import create_app
from app.models.user import Base, User


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app(create_tables=False)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


def test_register_creates_user_with_hashed_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "sales_user", "email": "sales@example.com", "password": "Password123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "sales_user"
    assert body["data"]["role"] == "USER"
    assert "password" not in body["data"]


def test_register_rejects_duplicate_username(client: TestClient) -> None:
    payload = {"username": "dup_user", "email": "dup1@example.com", "password": "Password123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "dup2@example.com"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "用户名或邮箱已存在"


def test_login_returns_access_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"username": "login_user", "email": "login@example.com", "password": "Password123"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "login_user", "password": "Password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["access_token"]


def test_swagger_token_endpoint_accepts_form_credentials(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"username": "swagger_user", "email": "swagger@example.com", "password": "Password123"},
    )

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "swagger_user", "password": "Password123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_me_requires_valid_token_and_returns_current_user(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": "me_user", "email": "me@example.com", "password": "Password123"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "me_user", "password": "Password123"},
    )
    token = login_response.json()["data"]["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": register_response.json()["data"]["id"],
        "username": "me_user",
        "email": "me@example.com",
        "role": "USER",
    }


def test_me_rejects_missing_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
