from collections.abc import Generator
from io import BytesIO

import pandas as pd
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


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"username": "dataset_user", "email": "dataset@example.com", "password": "Password123"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "dataset_user", "password": "Password123"},
    )
    token = login_response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_csv_returns_dataset_schema_and_preview(client: TestClient) -> None:
    csv_content = "date,region,sales_amount\n2026-07-01,华东,1200\n2026-07-02,华南,800\n"

    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(client),
        files={"file": ("sales.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["row_count"] == 2
    assert body["data"]["column_count"] == 3
    assert body["data"]["columns"][2]["name"] == "sales_amount"
    assert body["data"]["preview"][0]["region"] == "华东"


def test_upload_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("sales.csv", BytesIO("region\n华东\n".encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 401


def test_upload_rejects_unsupported_file_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(client),
        files={"file": ("notes.txt", BytesIO(b"not a data file"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "仅支持 CSV 或 XLSX 文件"


def test_upload_xlsx_returns_preview(client: TestClient) -> None:
    content = BytesIO()
    pd.DataFrame({"region": ["华东"], "sales_amount": [1000]}).to_excel(content, index=False)

    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(client),
        files={"file": ("sales.xlsx", BytesIO(content.getvalue()), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 201
    assert response.json()["data"]["preview"] == [{"region": "华东", "sales_amount": 1000}]


def test_upload_gbk_csv_uses_encoding_fallback(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(client),
        files={"file": ("sales.csv", BytesIO("区域,销售额\n华北,900\n".encode("gbk")), "text/csv")},
    )

    assert response.status_code == 201
    assert response.json()["data"]["preview"] == [{"区域": "华北", "销售额": 900}]
