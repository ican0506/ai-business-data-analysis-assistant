from __future__ import annotations

import pandas as pd

from app.services.analysis_planner import (
    AnalysisCapability,
    AnalysisPlanner,
    ORDER_ANALYSIS_CAPABILITIES,
)


def plan_by_id(available_fields: set[str]) -> dict[str, dict[str, object]]:
    planner = AnalysisPlanner()
    return {
        item["id"]: item
        for item in planner.plan(available_fields, ORDER_ANALYSIS_CAPABILITIES)
    }


def test_full_order_fields_support_all_capabilities() -> None:
    dataframe = pd.DataFrame(
        {
            "order_id": ["O-001"],
            "product": ["Laptop"],
            "quantity": [2],
            "sales_amount": [12000],
            "unit_price": [6000],
            "target_amount": [13000],
            "region": ["East"],
            "date": ["2026-08-01"],
            "customer_id": ["C-001"],
            "status": ["completed"],
        }
    )

    available_fields = AnalysisPlanner.available_fields_from_dataframe(dataframe)
    results = plan_by_id(available_fields)

    assert all(
        results[capability_id]["supported"] is True
        for capability_id in {
            "order_count", "product_quantity", "product_sales", "sales_total",
            "region_sales", "sales_trend", "target_completion", "customer_analysis",
            "status_analysis", "refund_analysis", "data_quality_analysis",
        }
    )
    assert results["category_analysis"]["supported"] is False
    assert results["payment_method_analysis"]["supported"] is False
    assert results["discount_analysis"]["supported"] is False
    assert results["sales_total"]["matched_fields"] == ["sales_amount"]


def test_simplified_order_fields_only_support_matching_capabilities() -> None:
    dataframe = pd.DataFrame(
        {
            "order_id": ["O-001"],
            "product": ["Laptop"],
            "quantity": [2],
            "date": ["2026-08-01"],
        }
    )

    results = plan_by_id(AnalysisPlanner.available_fields_from_dataframe(dataframe))

    assert results["order_count"]["supported"] is True
    assert results["product_quantity"]["supported"] is True
    assert results["sales_total"]["supported"] is False
    assert results["region_sales"]["supported"] is False
    assert results["sales_trend"]["supported"] is False
    assert results["customer_analysis"]["supported"] is False
    assert results["refund_analysis"]["supported"] is False


def test_any_of_uses_first_available_declared_solution() -> None:
    dataframe = pd.DataFrame(
        {
            "order_id": ["O-001"],
            "product": ["Laptop"],
            "quantity": [2],
            "unit_price": [6000],
            "date": ["2026-08-01"],
        }
    )

    results = plan_by_id(AnalysisPlanner.available_fields_from_dataframe(dataframe))

    assert results["sales_total"]["supported"] is True
    assert results["sales_total"]["matched_fields"] == ["unit_price", "quantity"]
    assert results["sales_trend"]["supported"] is True
    assert results["sales_trend"]["matched_fields"] == ["date", "unit_price", "quantity"]


def test_dataframe_availability_only_uses_real_pandas_missing_values() -> None:
    all_null_dataframe = pd.DataFrame({"sales_amount": [None, None, None]})
    partial_null_dataframe = pd.DataFrame({"sales_amount": [100, None, 200, None]})
    string_dataframe = pd.DataFrame({"sales_amount": ["", "N/A", "null"]})

    assert "sales_amount" not in AnalysisPlanner.available_fields_from_dataframe(
        all_null_dataframe
    )
    assert "sales_amount" in AnalysisPlanner.available_fields_from_dataframe(
        partial_null_dataframe
    )
    assert "sales_amount" in AnalysisPlanner.available_fields_from_dataframe(
        string_dataframe
    )


def test_any_of_uses_best_missing_candidate_and_keeps_declaration_order_on_tie() -> None:
    results = plan_by_id({"quantity"})

    assert results["sales_total"]["supported"] is False
    assert results["sales_total"]["missing_fields"] == ["sales_amount"]


def test_all_of_and_any_of_are_required_together() -> None:
    capability = AnalysisCapability(
        id="region_sales",
        name="区域销售分析",
        all_of=("region",),
        any_of=(("sales_amount",), ("unit_price", "quantity")),
    )
    planner = AnalysisPlanner()

    supported = planner.plan({"region", "unit_price", "quantity"}, (capability,))[0]
    unsupported = planner.plan({"sales_amount"}, (capability,))[0]

    assert supported["supported"] is True
    assert supported["matched_fields"] == ["region", "unit_price", "quantity"]
    assert unsupported["supported"] is False
    assert unsupported["missing_fields"] == ["region"]


def test_empty_dataframe_has_no_available_fields_and_does_not_raise() -> None:
    available_fields = AnalysisPlanner.available_fields_from_dataframe(pd.DataFrame())
    results = plan_by_id(available_fields)

    assert available_fields == set()
    assert all(
        result["supported"] is False
        for capability_id, result in results.items()
        if capability_id != "data_quality_analysis"
    )
    assert results["data_quality_analysis"]["supported"] is True


def test_target_completion_requires_target_and_a_sales_solution() -> None:
    planner = AnalysisPlanner()
    results = {
        item["id"]: item
        for item in planner.plan(
            {"target_amount", "unit_price", "quantity"},
            ORDER_ANALYSIS_CAPABILITIES,
        )
    }

    assert results["target_completion"]["supported"] is True
    assert results["target_completion"]["matched_fields"] == [
        "target_amount",
        "unit_price",
        "quantity",
    ]
