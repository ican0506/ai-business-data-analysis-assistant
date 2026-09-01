from __future__ import annotations

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
from app.services.canonical_field_mapper import CanonicalFieldMapper
from app.services.metrics_service import MetricsService


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
        json={"username": "mapping_user", "email": "mapping@example.com", "password": "Password123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "mapping_user", "password": "Password123"},
    )
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def upload_and_clean(client: TestClient, headers: dict[str, str], content: str, filename: str) -> int:
    upload = client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": (filename, BytesIO(content.encode("utf-8")), "text/csv")},
    )
    dataset_id = upload.json()["data"]["id"]
    cleaned = client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)
    assert cleaned.status_code == 201
    return dataset_id


def test_mapper_override_wins_over_automatic_alias_and_marks_methods() -> None:
    frame = pd.DataFrame({"总评": [90], "成绩": [80], "课程名": ["数学"]})

    mapped, metadata = CanonicalFieldMapper().map_dataframe(
        frame,
        overrides={"总评": "score", "课程名": "subject"},
    )

    assert list(mapped.columns) == ["score", "成绩", "subject"]
    assert metadata["mappings"] == [
        {"source": "总评", "target": "score", "method": "override"},
        {"source": "课程名", "target": "subject", "method": "override"},
    ]
    assert metadata["conflicts"] == [
        {
            "target": "score",
            "sources": ["总评", "成绩"],
            "reason": "automatic mapping suppressed by override",
        }
    ]


def test_mapper_rejects_duplicate_targets_and_existing_canonical_conflict() -> None:
    mapper = CanonicalFieldMapper()

    with pytest.raises(ValueError, match='multiple source columns map to canonical field "score"'):
        mapper.map_dataframe(pd.DataFrame({"总评": [90], "平时成绩": [80]}), overrides={"总评": "score", "平时成绩": "score"})
    with pytest.raises(ValueError, match="target canonical field already exists in dataset"):
        mapper.map_dataframe(pd.DataFrame({"score": [90], "总评": [80]}), overrides={"总评": "score"})


def test_put_mapping_persists_student_score_override_and_metrics_uses_it(client: TestClient) -> None:
    headers = auth_headers(client)
    dataset_id = upload_and_clean(
        client,
        headers,
        "学生编号,课程名,总评\n001,数学,90\n001,英语,80\n002,数学,85\n",
        "scores.csv",
    )

    saved = client.put(
        f"/api/v1/datasets/{dataset_id}/field-mapping",
        headers=headers,
        json={"overrides": {"学生编号": "student_id", "课程名": "subject", "总评": "score"}},
    )
    metrics = client.get(f"/api/v1/datasets/{dataset_id}/metrics", headers=headers)

    assert saved.status_code == 200
    assert metrics.status_code == 200
    data = metrics.json()["data"]
    assert data["selected_module"]["id"] == "student_score"
    assert data["student_score_analysis"]["student_count"] == 2
    assert data["student_score_analysis"]["score_summary"]["average"] == 85.0
    assert data["student_score_analysis"]["subject_score"][0]["name"] == "数学"
    assert {item["method"] for item in data["field_mapping"]["mappings"]} == {"override"}


def test_put_mapping_persists_order_override_and_keeps_derived_sales(client: TestClient) -> None:
    headers = auth_headers(client)
    dataset_id = upload_and_clean(
        client,
        headers,
        "单号,货品,件数,成交价\nO001,A,2,10\nO002,B,3,20\n",
        "orders.csv",
    )

    response = client.put(
        f"/api/v1/datasets/{dataset_id}/field-mapping",
        headers=headers,
        json={"overrides": {"单号": "order_id", "货品": "product", "件数": "quantity", "成交价": "unit_price"}},
    )
    metrics = client.get(f"/api/v1/datasets/{dataset_id}/metrics", headers=headers)

    assert response.status_code == 200
    assert metrics.json()["data"]["selected_module"]["id"] == "order"
    assert metrics.json()["data"]["sales_amount"]["total"] == 80.0


def test_get_mapping_returns_all_cleaned_order_source_columns(client: TestClient) -> None:
    headers = auth_headers(client)
    dataset_id = upload_and_clean(
        client,
        headers,
        "order_id,order_date,product_name,category,region,unit_price,quantity,discount,order_amount\n"
        "O001,2026-09-01,键盘,数码,华东,100,2,0.9,180\n",
        "complete-orders.csv",
    )

    response = client.get(f"/api/v1/datasets/{dataset_id}/field-mapping", headers=headers)

    assert response.status_code == 200
    fields = response.json()["data"]["field_mapping"]["fields"]
    assert [item["source"] for item in fields] == [
        "order_id", "order_date", "product_name", "category", "region",
        "unit_price", "quantity", "discount", "order_amount",
    ]
    assert {item["source"]: item["target"] for item in fields} == {
        "order_id": "order_id", "order_date": "date", "product_name": "product",
        "category": "category", "region": "region", "unit_price": "unit_price",
        "quantity": "quantity", "discount": "discount", "order_amount": "sales_amount",
    }


def test_put_mapping_persists_inventory_override_and_metrics_uses_it(client: TestClient) -> None:
    headers = auth_headers(client)
    dataset_id = upload_and_clean(
        client,
        headers,
        "SKU编码,现存数量,警戒库存\nSKU-1,5,10\nSKU-2,20,10\n",
        "inventory.csv",
    )

    response = client.put(
        f"/api/v1/datasets/{dataset_id}/field-mapping",
        headers=headers,
        json={"overrides": {"SKU编码": "product_id", "现存数量": "stock_quantity", "警戒库存": "safety_stock"}},
    )
    metrics = client.get(f"/api/v1/datasets/{dataset_id}/metrics", headers=headers)

    assert response.status_code == 200
    data = metrics.json()["data"]
    assert data["selected_module"]["id"] == "inventory"
    assert data["inventory_analysis"]["inventory_count"] == 2
    assert data["inventory_analysis"]["stock_summary"]["total"] == 25.0
    assert data["inventory_analysis"]["low_stock_analysis"][0]["product_id"] == "SKU-1"
    assert data["sales_amount"] is None
    assert data["student_score_analysis"] is None


def test_put_rejects_invalid_target_missing_source_and_duplicate_target(client: TestClient) -> None:
    headers = auth_headers(client)
    dataset_id = upload_and_clean(client, headers, "总评,平时成绩\n90,80\n", "invalid.csv")
    url = f"/api/v1/datasets/{dataset_id}/field-mapping"

    invalid_target = client.put(url, headers=headers, json={"overrides": {"总评": "not_a_target"}})
    missing_source = client.put(url, headers=headers, json={"overrides": {"不存在": "score"}})
    duplicate_target = client.put(url, headers=headers, json={"overrides": {"总评": "score", "平时成绩": "score"}})

    assert invalid_target.status_code == 400
    assert missing_source.status_code == 400
    assert duplicate_target.status_code == 400


def test_invalid_full_replacement_keeps_previous_overrides(client: TestClient) -> None:
    headers = auth_headers(client)
    dataset_id = upload_and_clean(client, headers, "总评,课程名称\n90,数学\n", "atomic.csv")
    url = f"/api/v1/datasets/{dataset_id}/field-mapping"

    initial = client.put(
        url,
        headers=headers,
        json={"overrides": {"总评": "score", "课程名称": "subject"}},
    )
    rejected = client.put(
        url,
        headers=headers,
        json={"overrides": {"总评": "not_a_target"}},
    )
    current = client.get(url, headers=headers)

    assert initial.status_code == 200
    assert rejected.status_code == 400
    assert current.json()["data"]["overrides"] == {"总评": "score", "课程名称": "subject"}


def test_put_empty_overrides_clears_only_current_dataset_and_get_returns_runtime_preview(client: TestClient) -> None:
    headers = auth_headers(client)
    first = upload_and_clean(client, headers, "总评\n90\n", "first.csv")
    second = upload_and_clean(client, headers, "总评\n80\n", "second.csv")

    client.put(f"/api/v1/datasets/{first}/field-mapping", headers=headers, json={"overrides": {"总评": "score"}})
    isolated = client.get(f"/api/v1/datasets/{second}/field-mapping", headers=headers)
    cleared = client.put(f"/api/v1/datasets/{first}/field-mapping", headers=headers, json={"overrides": {}})
    preview = client.get(f"/api/v1/datasets/{first}/field-mapping", headers=headers)

    assert isolated.status_code == 200
    assert isolated.json()["data"]["overrides"] == {}
    assert cleared.status_code == 200
    assert preview.json()["data"]["overrides"] == {}
    assert preview.json()["data"]["field_mapping"]["mappings"] == []


def test_metrics_service_accepts_overrides_without_changing_source_dataframe() -> None:
    frame = pd.DataFrame({"学生编号": ["001"], "课程名": ["数学"], "总评": [0]})
    before = frame.copy(deep=True)

    metrics = MetricsService()._build_metrics_from_frame(
        frame,
        dataset_id=1,
        field_overrides={"学生编号": "student_id", "课程名": "subject", "总评": "score"},
    )

    assert frame.equals(before)
    assert metrics["selected_module"]["id"] == "student_score"
    assert metrics["student_score_analysis"]["score_summary"]["average"] == 0.0
