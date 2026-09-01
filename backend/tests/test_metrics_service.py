from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from app.services.metrics_service import MetricsService


def build_metrics(data: dict[str, list[object]]) -> dict:
    return MetricsService()._build_metrics_from_frame(pd.DataFrame(data), dataset_id=1)


def plan_by_id(metrics: dict) -> dict[str, dict]:
    return {item["id"]: item for item in metrics["analysis_plan"]}


def test_full_sales_data_keeps_existing_metrics_and_reports_capabilities() -> None:
    metrics = build_metrics(
        {
            "order_id": ["O-1", "O-2", "O-3"],
            "product": ["A", "A", "B"],
            "quantity": [2, 3, 1],
            "unit_price": [50, 200 / 3, 150],
            "sales_amount": [100, 200, 150],
            "target_amount": [120, 220, 160],
            "region": ["east", "east", "south"],
            "date": ["2026-08-01", "2026-08-02", "2026-08-03"],
        }
    )

    assert metrics["available_fields"] == [
            "order_id", "product", "quantity", "unit_price", "sales_amount", "target_amount", "region", "date"
    ]
    assert metrics["sales_amount"]["total"] == 450.0
    assert metrics["completion_rate"] == 90.0
    assert metrics["growth_rate"] == 50.0
    assert metrics["region_ranking"][0] == {"name": "east", "value": 300.0}
    assert metrics["order_count"] == 3
    assert metrics["product_quantity"] == [
        {"name": "A", "value": 5.0},
        {"name": "B", "value": 1.0},
    ]
    assert plan_by_id(metrics)["target_completion"]["supported"] is True


def test_missing_sales_amount_returns_unavailable_metrics_not_zero() -> None:
    metrics = build_metrics(
        {
            "order_id": ["O-1", "O-2"],
            "product": ["A", "B"],
            "quantity": [2, 3],
            "date": ["2026-08-01", "2026-08-02"],
        }
    )

    assert metrics["sales_amount"] is None
    assert metrics["growth_rate"] is None
    assert metrics["region_ranking"] == []
    assert metrics["order_count"] == 2
    assert metrics["product_quantity"] == [
        {"name": "B", "value": 3.0},
        {"name": "A", "value": 2.0},
    ]


def test_unit_price_and_quantity_create_in_memory_sales_amount() -> None:
    metrics = build_metrics(
        {
            "unit_price": [10, 20],
            "quantity": [2, 3],
            "date": ["2026-08-01", "2026-08-02"],
        }
    )

    assert metrics["sales_amount"]["total"] == 80.0
    assert metrics["growth_rate"] == 200.0
    assert plan_by_id(metrics)["sales_total"]["matched_fields"] == [
        "unit_price", "quantity"
    ]


def test_region_and_date_dependent_metrics_are_skipped_independently() -> None:
    without_region = build_metrics(
        {
            "sales_amount": [100, 200], "unit_price": [50, 100], "quantity": [2, 2],
            "date": ["2026-08-01", "2026-08-02"],
        }
    )
    without_date = build_metrics(
        {
            "sales_amount": [100, 200], "unit_price": [50, 100], "quantity": [2, 2],
            "region": ["east", "south"],
        }
    )

    assert without_region["sales_amount"]["total"] == 300.0
    assert without_region["region_ranking"] == []
    assert without_region["top_regions"] == []
    assert without_region["highest_sales_region"] is None
    assert without_region["lowest_sales_region"] is None
    assert without_date["sales_amount"]["total"] == 300.0
    assert without_date["growth_rate"] is None


def test_null_sales_uses_alternative_only_when_it_is_available() -> None:
    unavailable = build_metrics({"sales_amount": [None, None]})
    derived = build_metrics(
        {"sales_amount": [None, None], "unit_price": [10, 20], "quantity": [2, 3]}
    )

    assert unavailable["sales_amount"] is None
    assert plan_by_id(unavailable)["sales_total"]["supported"] is False
    assert derived["sales_amount"]["total"] == 80.0
    assert plan_by_id(derived)["sales_total"]["matched_fields"] == [
        "unit_price", "quantity"
    ]


def test_target_is_optional_for_region_sales_but_required_for_completion() -> None:
    metrics = build_metrics(
        {
            "sales_amount": [100, 200], "unit_price": [50, 100], "quantity": [2, 2],
            "region": ["east", "south"],
        }
    )

    assert metrics["completion_rate"] is None
    assert metrics["region_performance"] == [
        {"name": "south", "sales_amount": 200.0, "target_amount": None, "completion_rate": None},
        {"name": "east", "sales_amount": 100.0, "target_amount": None, "completion_rate": None},
    ]
    assert plan_by_id(metrics)["target_completion"]["supported"] is False


def test_student_score_data_does_not_run_order_metrics() -> None:
    metrics = build_metrics(
        {
            "student_id": ["S-1", "S-2"],
            "subject": ["math", "english"],
            "score": [95, 88],
        }
    )

    assert metrics["selected_module"]["id"] == "student_score"
    assert metrics["sales_amount"] is None
    assert metrics["growth_rate"] is None
    assert metrics["completion_rate"] is None
    assert metrics["top_regions"] == []
    assert metrics["region_ranking"] == []
    assert metrics["order_count"] is None
    assert metrics["product_quantity"] == []
    assert plan_by_id(metrics)["score_summary"]["supported"] is True
    assert metrics["student_score_analysis"] == {
        "student_count": 2,
        "score_summary": {
            "count": 2,
            "average": 91.5,
            "maximum": 95.0,
            "minimum": 88.0,
            "median": 91.5,
        },
        "subject_score": [
            {"name": "math", "count": 1, "average": 95.0, "maximum": 95.0, "minimum": 95.0},
            {"name": "english", "count": 1, "average": 88.0, "maximum": 88.0, "minimum": 88.0},
        ],
        "class_score": [],
        "student_score": [
            {"student_id": "S-1", "score_count": 1, "average": 95.0, "maximum": 95.0, "minimum": 95.0},
            {"student_id": "S-2", "score_count": 1, "average": 88.0, "maximum": 88.0, "minimum": 88.0},
        ],
        "exam_trend": [],
    }


def test_generic_data_returns_base_profile_without_order_metrics() -> None:
    metrics = build_metrics(
        {
            "location_label": ["Shanghai", None],
            "temperature": [30, None],
            "timestamp": ["2026-08-01", "2026-08-02"],
        }
    )

    assert metrics["selected_module"]["id"] == "generic"
    assert metrics["sales_amount"] is None
    assert metrics["order_count"] is None
    assert metrics["product_quantity"] == []
    assert metrics["generic_analysis"] == {
        "row_count": 2,
        "column_profile": [
                {"name": "location_label", "dtype": "object", "non_null_count": 1, "null_count": 1},
            {"name": "temperature", "dtype": "float64", "non_null_count": 1, "null_count": 1},
            {"name": "timestamp", "dtype": "object", "non_null_count": 2, "null_count": 0},
        ],
        "missing_value_analysis": [
                {"column": "location_label", "missing_count": 1, "missing_rate": 50.0},
            {"column": "temperature", "missing_count": 1, "missing_rate": 50.0},
            {"column": "timestamp", "missing_count": 0, "missing_rate": 0.0},
        ],
    }


def test_empty_dataframe_safely_uses_generic_module() -> None:
    metrics = build_metrics({})

    assert metrics["selected_module"]["id"] == "generic"
    assert metrics["generic_analysis"] == {
        "row_count": 0,
        "column_profile": [],
        "missing_value_analysis": [],
    }


def test_chinese_student_headers_run_real_student_score_analysis_on_mapped_frame() -> None:
    metrics = build_metrics(
        {
            "学号": ["001", "001", "002"],
            "姓名": ["张三", "张三", "李四"],
            "科目": ["数学", "英语", "数学"],
            "成绩": [90, 80, 85],
            "班级": ["一班", "一班", "一班"],
        }
    )

    assert metrics["selected_module"]["id"] == "student_score"
    assert metrics["student_score_analysis"]["student_count"] == 2
    assert metrics["student_score_analysis"]["score_summary"]["average"] == 85.0
    assert metrics["student_score_analysis"]["subject_score"] == [
        {"name": "数学", "count": 2, "average": 87.5, "maximum": 90.0, "minimum": 85.0},
        {"name": "英语", "count": 1, "average": 80.0, "maximum": 80.0, "minimum": 80.0},
    ]
    assert metrics["field_mapping"]["unmapped_columns"] == []


def test_chinese_order_headers_keep_derived_sales_calculation_on_mapped_frame() -> None:
    metrics = build_metrics(
        {
            "订单编号": ["O-1", "O-2"],
            "商品名称": ["A", "B"],
            "数量": [2, 3],
            "单价": [10, 20],
            "区域": ["华东", "华南"],
        }
    )

    assert metrics["selected_module"]["id"] == "order"
    assert metrics["sales_amount"]["total"] == 80.0
    assert metrics["region_ranking"] == [
        {"name": "华南", "value": 60.0},
        {"name": "华东", "value": 20.0},
    ]
    assert metrics["field_mapping"]["mappings"][0] == {
        "source": "订单编号",
        "target": "order_id",
        "method": "automatic",
    }


def test_real_ecommerce_headers_run_order_analysis_with_trusted_amount() -> None:
    metrics = build_metrics(
        {
            "order_id": ["O-1", "O-2"], "user_id": ["U-1", "U-2"],
            "city": ["郑州市", "洛阳市"], "product": ["鼠标", "键盘"],
            "商品分类": ["数码", "数码"], "unit_price": [100, 50], "quantity": [2, 1],
            "discount": [0.9, 1], "order_amount": [999, 50], "order_status": ["已完成", "已退款"],
            "order_time": ["2026-08-01", "2026-08-02"], "payment_method": ["微信", "支付宝"],
            "phone": ["13800000000", "13900000000"], "email": ["a@example.com", "b@example.com"],
        }
    )

    assert metrics["selected_module"]["id"] == "order"
    assert metrics["sales_amount"]["total"] == 230.0
    assert metrics["order_analysis"]["overview"]["amount_mismatch_count"] == 1
    assert metrics["order_analysis"]["region_analysis"][0]["name"] == "郑州"
    assert metrics["order_analysis"]["status_summary"]["refund_order_count"] == 1
    assert "phone" not in metrics["field_mapping"]["unmapped_columns"]
    assert "email" not in metrics["field_mapping"]["unmapped_columns"]
    assert all("phone" not in item.get("matched_fields", []) for item in metrics["analysis_plan"])


def test_unknown_chinese_columns_remain_generic_and_are_reported_as_unmapped() -> None:
    metrics = build_metrics({"地点标签": ["上海"], "温度": [30], "备注": ["晴"]})

    assert metrics["selected_module"]["id"] == "generic"
    assert metrics["generic_analysis"]["column_profile"][0]["name"] == "地点标签"
    assert metrics["field_mapping"] == {
        "mappings": [],
        "unmapped_columns": ["地点标签", "温度", "备注"],
        "conflicts": [],
        "fields": [
            {"source": "地点标签", "target": None, "method": "unmapped"},
            {"source": "温度", "target": None, "method": "unmapped"},
            {"source": "备注", "target": None, "method": "unmapped"},
        ],
    }


def test_chinese_inventory_data_runs_inventory_analysis_without_order_or_student_metrics() -> None:
    metrics = build_metrics(
        {
            "商品编号": ["P001", "P002"],
            "商品名称": ["商品A", "商品B"],
            "库存数量": [5, 30],
            "安全库存": [10, 15],
            "单位成本": [20, 12],
            "仓库": ["郑州仓", "郑州仓"],
        }
    )

    assert metrics["selected_module"]["id"] == "inventory"
    assert metrics["inventory_analysis"]["inventory_count"] == 2
    assert metrics["inventory_analysis"]["inventory_value"]["total"] == 460.0
    assert metrics["inventory_analysis"]["low_stock_analysis"][0]["product_id"] == "P001"
    assert metrics["inventory_analysis"]["warehouse_stock"] == [{"name": "郑州仓", "value": 35.0}]
    assert metrics["sales_amount"] is None
    assert metrics["student_score_analysis"] is None


def test_build_metrics_uses_the_latest_cleaning_run_file(monkeypatch, tmp_path) -> None:
    storage_root = tmp_path / "storage"
    storage_root.mkdir()
    (storage_root / "run-1.csv").write_text("order_id,unit_price,quantity\nO-1,10,10\n", encoding="utf-8-sig")
    (storage_root / "run-2.csv").write_text("order_id,unit_price,quantity\nO-1,20,10\n", encoding="utf-8-sig")
    newest_run = SimpleNamespace(dataset_id=7, cleaned_storage_path="run-2.csv")
    db = SimpleNamespace(scalar=lambda _statement: newest_run)
    monkeypatch.setattr(
        "app.services.metrics_service.get_settings",
        lambda: SimpleNamespace(resolved_storage_root=storage_root),
    )

    metrics = MetricsService(
        override_service=SimpleNamespace(get_overrides=lambda *_args: {})
    ).build_metrics(db, SimpleNamespace(id=7))

    assert metrics["dataset_id"] == 7
    assert metrics["sales_amount"]["total"] == 200.0
