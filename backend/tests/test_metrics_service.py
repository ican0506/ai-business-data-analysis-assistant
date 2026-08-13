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
