from collections.abc import Generator
from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
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


def auth_headers_for(client: TestClient, username: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "Password123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "Password123"},
    )
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_list_datasets_returns_only_the_current_users_records(client: TestClient) -> None:
    owner_headers = auth_headers_for(client, "dataset_owner")
    other_headers = auth_headers_for(client, "dataset_other")
    for filename in ("orders.csv", "orders.csv"):
        response = client.post(
            "/api/v1/datasets/upload",
            headers=owner_headers,
            files={"file": (filename, BytesIO(b"order_id,unit_price,quantity\nO-1,10,2\n"), "text/csv")},
        )
        assert response.status_code == 201

    owner_response = client.get("/api/v1/datasets", headers=owner_headers)
    other_response = client.get("/api/v1/datasets", headers=other_headers)

    assert owner_response.status_code == 200
    assert owner_response.json()["message"] == "数据集列表读取成功"
    assert [item["original_filename"] for item in owner_response.json()["data"]] == ["orders.csv", "orders.csv"]
    assert all({"id", "original_filename", "status", "row_count", "column_count", "created_at"} <= item.keys() for item in owner_response.json()["data"])
    assert other_response.json()["data"] == []


def test_other_user_cannot_access_dataset_metrics_mapping_analysis_or_reports(client: TestClient) -> None:
    owner_headers = auth_headers_for(client, "access_owner")
    other_headers = auth_headers_for(client, "access_other")
    upload = client.post(
        "/api/v1/datasets/upload",
        headers=owner_headers,
        files={"file": ("orders.csv", BytesIO(b"order_id,unit_price,quantity\nO-1,10,2\n"), "text/csv")},
    )
    dataset_id = upload.json()["data"]["id"]
    assert client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=owner_headers).status_code == 201

    for method, path in (
        ("get", f"/api/v1/datasets/{dataset_id}/metrics"),
        ("get", f"/api/v1/datasets/{dataset_id}/field-mapping"),
        ("post", f"/api/v1/datasets/{dataset_id}/ai-analysis"),
        ("get", f"/api/v1/datasets/{dataset_id}/reports/excel"),
        ("get", f"/api/v1/datasets/{dataset_id}/reports/word"),
        ("get", f"/api/v1/datasets/{dataset_id}/reports/pdf"),
    ):
        response = getattr(client, method)(path, headers=other_headers)
        assert response.status_code == 403
        if "/reports/" in path:
            assert response.json()["detail"] == "无权下载此数据集报告。"


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


def test_upload_rejects_csv_with_header_only(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(client),
        files={"file": ("empty.csv", BytesIO("姓名,城市\n".encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "数据文件不包含可分析的数据行"


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


def test_clean_dataset_standardizes_sales_columns_and_removes_invalid_rows(client: TestClient) -> None:
    csv_content = (
        "日期,区域,销售额,目标额\n"
        "2026/07/01,华东,\"1,200\",1500\n"
        "2026/07/01,华东,\"1,200\",1500\n"
        ",,,\n"
        "2026-07-02,华南,800,1000\n"
    )
    headers = auth_headers(client)
    upload_response = client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": ("sales.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )

    response = client.post(
        f"/api/v1/datasets/{upload_response.json()['data']['id']}/clean",
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["original_row_count"] == 4
    assert body["data"]["cleaned_row_count"] == 2
    assert body["data"]["removed_empty_rows"] == 1
    assert body["data"]["removed_duplicate_rows"] == 1
    assert body["data"]["columns"] == ["date", "region", "sales_amount", "target_amount"]
    assert body["data"]["preview"][0]["sales_amount"] == 1200


def test_get_dataset_metrics_returns_sales_summary_and_region_ranking(client: TestClient) -> None:
    csv_content = (
        "date,region,unit_price,quantity,sales_amount,target_amount\n"
        "2026-07-01,east,600,2,1200,1500\n"
        "2026-07-02,south,400,2,800,1000\n"
        "2026-07-03,east,900,2,1800,2000\n"
    )
    headers = auth_headers(client)
    upload_response = client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": ("sales.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    dataset_id = upload_response.json()["data"]["id"]
    client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)

    response = client.get(f"/api/v1/datasets/{dataset_id}/metrics", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_rows"] == 3
    assert data["sales_amount"]["average"] == 1266.67
    assert data["sales_amount"]["maximum"] == 1800
    assert data["completion_rate"] == 84.44
    assert data["top_regions"][0] == {"name": "east", "value": 3000}
    assert data["highest_sales_region"] == {"name": "east", "value": 3000}
    assert data["lowest_sales_region"] == {"name": "south", "value": 800}
    assert data["region_performance"] == [
        {"name": "east", "sales_amount": 3000, "target_amount": 3500, "completion_rate": 85.71},
        {"name": "south", "sales_amount": 800, "target_amount": 1000, "completion_rate": 80.0},
    ]
    assert data["sales_volatility"]["coefficient_of_variation"] == 32.44


def test_generate_business_analysis_returns_structured_fallback_report(client: TestClient) -> None:
    csv_content = "date,region,unit_price,quantity,sales_amount,target_amount\n2026-07-01,east,400,2,800,1000\n2026-07-02,south,200,2,400,1000\n"
    headers = auth_headers(client)
    upload = client.post(
        "/api/v1/datasets/upload", headers=headers,
        files={"file": ("sales.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    dataset_id = upload.json()["data"]["id"]
    client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)

    response = client.post(f"/api/v1/datasets/{dataset_id}/ai-analysis", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["mode"] == "rule_based"
    assert data["summary"]
    assert data["anomalies"]
    assert data["recommendations"]
    assert any("\u5b8c\u6210\u7387" in item for item in data["anomalies"])
    assert any("\u73af\u6bd4\u4e0b\u964d" in item for item in data["anomalies"])
    assert any("\u533a\u57df" in item for item in data["business_problems"])


def test_export_excel_report_returns_workbook(client: TestClient) -> None:
    csv_content = "date,region,unit_price,quantity,sales_amount,target_amount\n2026-07-01,east,400,2,800,1000\n"
    headers = auth_headers(client)
    upload = client.post("/api/v1/datasets/upload", headers=headers, files={"file": ("sales.csv", BytesIO(csv_content.encode()), "text/csv")})
    dataset_id = upload.json()["data"]["id"]
    client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)

    response = client.get(f"/api/v1/datasets/{dataset_id}/reports/excel", headers=headers)

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument")
    workbook = load_workbook(BytesIO(response.content))
    assert workbook.active._charts


@pytest.mark.parametrize(("report_type", "content_type"), [("word", "application/vnd.openxmlformats-officedocument"), ("pdf", "application/pdf")])
def test_export_word_and_pdf_reports(client: TestClient, report_type: str, content_type: str) -> None:
    csv_content = "date,region,unit_price,quantity,sales_amount,target_amount\n2026-07-01,east,400,2,800,1000\n"
    headers = auth_headers(client)
    upload = client.post("/api/v1/datasets/upload", headers=headers, files={"file": ("sales.csv", BytesIO(csv_content.encode()), "text/csv")})
    dataset_id = upload.json()["data"]["id"]
    client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)
    response = client.get(f"/api/v1/datasets/{dataset_id}/reports/{report_type}", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(content_type)
    if report_type == "word":
        with ZipFile(BytesIO(response.content)) as document:
            assert any(name.startswith("word/media/") for name in document.namelist())
