from __future__ import annotations

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
            "sales_amount": [100, 200, 150],
            "target_amount": [120, 220, 160],
            "region": ["east", "east", "south"],
            "date": ["2026-08-01", "2026-08-02", "2026-08-03"],
        }
    )

    assert metrics["available_fields"] == [
        "order_id", "product", "quantity", "sales_amount", "target_amount", "region", "date"
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
        {"sales_amount": [100, 200], "date": ["2026-08-01", "2026-08-02"]}
    )
    without_date = build_metrics({"sales_amount": [100, 200], "region": ["east", "south"]})

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
    metrics = build_metrics({"sales_amount": [100, 200], "region": ["east", "south"]})

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
            "city": ["Shanghai", None],
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
            {"name": "city", "dtype": "object", "non_null_count": 1, "null_count": 1},
            {"name": "temperature", "dtype": "float64", "non_null_count": 1, "null_count": 1},
            {"name": "timestamp", "dtype": "object", "non_null_count": 2, "null_count": 0},
        ],
        "missing_value_analysis": [
            {"column": "city", "missing_count": 1, "missing_rate": 50.0},
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


def test_unknown_chinese_columns_remain_generic_and_are_reported_as_unmapped() -> None:
    metrics = build_metrics({"城市": ["上海"], "温度": [30], "备注": ["晴"]})

    assert metrics["selected_module"]["id"] == "generic"
    assert metrics["generic_analysis"]["column_profile"][0]["name"] == "城市"
    assert metrics["field_mapping"] == {
        "mappings": [],
        "unmapped_columns": ["城市", "温度", "备注"],
        "conflicts": [],
    }
