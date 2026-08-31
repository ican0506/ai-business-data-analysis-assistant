from __future__ import annotations

import pandas as pd
import pytest
from pydantic import ValidationError

from app.schemas.data_chat import (
    DataChatDateRange,
    DataChatFilters,
    DataChatMetric,
    DataChatQueryPlan,
    DataChatSort,
    DataChatSortDirection,
    DataChatGroupBy,
)
from app.services.analysis_planner import AnalysisPlanner
from app.analysis_modules.order import ORDER_ANALYSIS_CAPABILITIES
from app.services.data_chat.metric_query_engine import MetricQueryEngine
from app.services.order_analyzer import OrderAnalyzer


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4", "O-5", "O-5"],
            "product": ["手机", "手机", "耳机", "显示器", "耳机", "耳机"],
            "category": ["数码", "数码", "配件", "数码", "配件", "配件"],
            "region": ["华东", "华东", "华南", "华南", "华东", "华东"],
            "date": [
                "2026-05-01", "2026-05-15", "2026-06-01",
                "2026-06-15", "2026-07-01", "2026-07-01",
            ],
            "unit_price": [100, 200, 50, 300, 10, 10],
            "quantity": [2, 1, 4, 1, 5, 5],
            "sales_amount": [999, 200, 200, 300, 50, 50],
        }
    )


def _plan(**overrides: object) -> DataChatQueryPlan:
    values: dict[str, object] = {"metrics": [DataChatMetric.SALES_AMOUNT]}
    values.update(overrides)
    return DataChatQueryPlan(**values)


def test_query_plan_rejects_values_outside_the_whitelist() -> None:
    with pytest.raises(ValidationError):
        DataChatQueryPlan(metrics=["raw_sql"])
    with pytest.raises(ValidationError):
        _plan(group_by=["customer"])
    with pytest.raises(ValidationError):
        _plan(limit=0)
    with pytest.raises(ValidationError):
        _plan(date_range=DataChatDateRange(start="2026-06-01", end="2026-05-01"))


def test_engine_calculates_all_metrics_with_the_order_analyzer_definition() -> None:
    frame = _frame()
    result = MetricQueryEngine().query(
        frame,
        _plan(
            metrics=[
                DataChatMetric.SALES_AMOUNT,
                DataChatMetric.SALES_QUANTITY,
                DataChatMetric.ORDER_COUNT,
                DataChatMetric.AVERAGE_ORDER_VALUE,
            ]
        ),
    )

    order_plan = AnalysisPlanner().plan(
        AnalysisPlanner.available_fields_from_dataframe(frame), ORDER_ANALYSIS_CAPABILITIES
    )
    overview = OrderAnalyzer().analyze(frame, order_plan)["overview"]

    assert result["status"] == "success"
    assert result["metrics"] == {
        "sales_amount": overview["sales_total"],
        "sales_quantity": 13.0,
        "order_count": overview["order_count"],
        "average_order_value": overview["average_order_value"],
    }
    assert result["metrics"]["sales_amount"] == 950.0
    assert result["metrics"]["order_count"] == 5


def test_engine_filters_by_month_date_range_and_order_dimensions() -> None:
    engine = MetricQueryEngine()

    may = engine.query(
        _frame(),
        _plan(
            metrics=[DataChatMetric.SALES_AMOUNT, DataChatMetric.ORDER_COUNT],
            date_range=DataChatDateRange(start="2026-05-01", end="2026-05-31"),
        ),
    )
    east = engine.query(
        _frame(),
        _plan(
            metrics=[DataChatMetric.SALES_AMOUNT],
            filters=DataChatFilters(region="华东", product="手机", category="数码"),
        ),
    )

    assert may["metrics"] == {"sales_amount": 400.0, "order_count": 2}
    assert may["data_scope"]["date_range"] == {"start": "2026-05-01", "end": "2026-05-31"}
    assert east["metrics"] == {"sales_amount": 400.0}


def test_engine_returns_unavailable_instead_of_zero_for_missing_quantity() -> None:
    frame = _frame().drop(columns=["quantity"])

    result = MetricQueryEngine().query(
        frame,
        _plan(metrics=[DataChatMetric.SALES_QUANTITY]),
    )

    assert result["status"] == "unavailable"
    assert result["metrics"] == {}
    assert result["unavailable"] == [
        {
            "metric": "sales_quantity",
            "reason": "quantity 字段不可用于计算",
        }
    ]


def test_engine_returns_deterministic_product_category_and_region_top_n() -> None:
    engine = MetricQueryEngine()
    common = {
        "metrics": [DataChatMetric.SALES_AMOUNT],
        "sort": DataChatSort(metric=DataChatMetric.SALES_AMOUNT, direction=DataChatSortDirection.DESC),
        "limit": 2,
    }

    product = engine.query(_frame(), _plan(group_by=[DataChatGroupBy.PRODUCT], **common))
    category = engine.query(_frame(), _plan(group_by=[DataChatGroupBy.CATEGORY], **common))
    region = engine.query(_frame(), _plan(group_by=[DataChatGroupBy.REGION], **common))

    assert product["rows"] == [
        {"product": "手机", "sales_amount": 400.0},
        {"product": "显示器", "sales_amount": 300.0},
    ]
    assert category["rows"] == [
        {"category": "数码", "sales_amount": 700.0},
        {"category": "配件", "sales_amount": 250.0},
    ]
    assert region["rows"] == [
        {"region": "华南", "sales_amount": 500.0},
        {"region": "华东", "sales_amount": 450.0},
    ]


def test_engine_builds_monthly_sales_trend_in_calendar_order() -> None:
    result = MetricQueryEngine().query(
        _frame(),
        _plan(
            metrics=[DataChatMetric.SALES_AMOUNT],
            group_by=[DataChatGroupBy.MONTH],
        ),
    )

    assert result["rows"] == [
        {"month": "2026-05", "sales_amount": 400.0},
        {"month": "2026-06", "sales_amount": 500.0},
        {"month": "2026-07", "sales_amount": 50.0},
    ]


def test_engine_applies_user_field_overrides_before_order_calculation() -> None:
    frame = pd.DataFrame(
        {
            "单号": ["O-1", "O-2"],
            "货品": ["A", "B"],
            "件数": [2, 3],
            "成交价": [10, 20],
        }
    )

    result = MetricQueryEngine().query(
        frame,
        _plan(metrics=[DataChatMetric.SALES_AMOUNT, DataChatMetric.ORDER_COUNT]),
        field_overrides={
            "单号": "order_id",
            "货品": "product",
            "件数": "quantity",
            "成交价": "unit_price",
        },
    )

    assert result["metrics"] == {"sales_amount": 80.0, "order_count": 2}
    assert result["analysis_context"]["selected_module"]["id"] == "order"


def test_engine_keeps_real_zero_sales_distinct_from_unavailable_sales() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "unit_price": [0],
            "quantity": [2],
        }
    )

    result = MetricQueryEngine().query(frame, _plan())

    assert result["status"] == "success"
    assert result["metrics"] == {"sales_amount": 0.0}
    assert result["unavailable"] == []


def test_query_plan_rejects_grouped_average_order_value_without_a_defined_dimension_rule() -> None:
    with pytest.raises(ValidationError):
        _plan(
            metrics=[DataChatMetric.AVERAGE_ORDER_VALUE],
            group_by=[DataChatGroupBy.PRODUCT],
        )


def test_engine_marks_a_missing_group_dimension_as_unavailable() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "unit_price": [10],
            "quantity": [2],
        }
    )

    result = MetricQueryEngine().query(
        frame,
        _plan(metrics=[DataChatMetric.SALES_AMOUNT], group_by=[DataChatGroupBy.REGION]),
    )

    assert result["status"] == "unavailable"
    assert result["rows"] == []
    assert result["unavailable"] == [
        {"metric": "sales_amount", "reason": "region 字段不可用于分组"}
    ]


def test_sales_quantity_keeps_equal_values_from_distinct_order_rows() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3"],
            "product": ["A", "B", "C"],
            "quantity": [2, 2, 3],
            "unit_price": [10, 10, 10],
        }
    )

    result = MetricQueryEngine().query(
        frame,
        _plan(metrics=[DataChatMetric.SALES_QUANTITY]),
    )

    assert result["metrics"] == {"sales_quantity": 7.0}
