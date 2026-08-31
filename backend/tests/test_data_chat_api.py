from collections.abc import Generator
from io import BytesIO

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


def _headers(client: TestClient, username: str) -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"username": username, "email": f"{username}@example.com", "password": "Password123"})
    response = client.post("/api/v1/auth/login", json={"username": username, "password": "Password123"})
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _upload_and_clean(client: TestClient, headers: dict[str, str]) -> int:
    upload = client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": ("orders.csv", BytesIO("order_id,product,unit_price,quantity,date\nO-1,Phone,10,2,2026-05-01\n".encode()), "text/csv")},
    )
    dataset_id = upload.json()["data"]["id"]
    assert client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers).status_code == 201
    return dataset_id


def test_data_chat_api_queries_the_current_users_cleaned_order_dataset(client: TestClient) -> None:
    headers = _headers(client, "chat_owner")
    dataset_id = _upload_and_clean(client, headers)

    response = client.post(
        "/api/v1/data-chat/query",
        headers=headers,
        json={"dataset_id": dataset_id, "question": "2026年5月销售额是多少"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["interpreter_mode"] == "rule"
    assert payload["data"]["result"]["metrics"]["sales_amount"] == 20.0


def test_data_chat_api_requires_login_and_isolates_datasets(client: TestClient) -> None:
    owner_headers = _headers(client, "chat_owner_two")
    other_headers = _headers(client, "chat_other")
    dataset_id = _upload_and_clean(client, owner_headers)

    assert client.post("/api/v1/data-chat/query", json={"dataset_id": dataset_id, "question": "销售额是多少"}).status_code == 401
    response = client.post(
        "/api/v1/data-chat/query",
        headers=other_headers,
        json={"dataset_id": dataset_id, "question": "销售额是多少"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "无权查询此数据集"
