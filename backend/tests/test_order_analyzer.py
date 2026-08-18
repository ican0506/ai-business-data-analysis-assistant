from __future__ import annotations

import pandas as pd

from app.analysis_modules.order import ORDER_ANALYSIS_CAPABILITIES
from app.services.analysis_planner import AnalysisPlanner
from app.services.order_analyzer import OrderAnalyzer


def _plan(frame: pd.DataFrame) -> list[dict[str, object]]:
    return AnalysisPlanner().plan(
        AnalysisPlanner.available_fields_from_dataframe(frame),
        ORDER_ANALYSIS_CAPABILITIES,
    )


def test_order_analyzer_uses_trusted_amount_and_keeps_duplicate_quality_facts() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4", "O-2"],
            "customer_id": ["U-1", "U-1", "U-2", "U-3", "U-1"],
            "customer_name": ["张三", "张三", "李四", "王五", "张三"],
            "product": ["鼠标", "键盘", "显示器", "鼠标", "键盘"],
            "category": ["数码", "数码", "办公", "数码", "数码"],
            "region": ["郑州市", " luoyang ", "郑州", "洛阳市", " luoyang "],
            "unit_price": [100, 50, -10, 0, 50],
            "quantity": [2, 1, 1, 0, 1],
            "discount": [0.9, None, 1, 0, None],
            "sales_amount": [999, 40, 60, 0, 40],
            "status": ["已完成", "completed", "已取消", "已退款", "completed"],
            "payment_method": ["微信", "支付宝", "银行卡", "微信", "支付宝"],
            "date": ["2026/08/03", "2026-08-01", "bad-date", "2026-08-04", "2026-08-01"],
            "gender": ["男", "male", "女", None, "male"],
            "age": [25, 30, 130, 0, 30],
        }
    )

    analysis = OrderAnalyzer().analyze(frame, _plan(frame))
    overview = analysis["overview"]

    assert overview["record_count"] == 5
    assert overview["order_count"] == 4
    assert overview["sales_total"] == 280.0
    assert overview["average_order_value"] == 70.0
    assert overview["amount_mismatch_count"] == 1
    assert overview["amount_mismatch_rate"] == 25.0
    assert analysis["product_analysis"][0] == {
        "name": "鼠标",
        "order_count": 2,
        "quantity": 2.0,
        "sales_amount": 180.0,
    }
    assert analysis["region_analysis"][0]["name"] == "郑州"
    assert analysis["customer_analysis"]["unique_customer_count"] == 3
    assert analysis["customer_analysis"]["repeat_customer_count"] == 1
    assert analysis["status_summary"] == {
        "completed_order_count": 2,
        "cancelled_order_count": 1,
        "refund_order_count": 1,
        "order_completion_rate": 50.0,
        "cancellation_rate": 25.0,
        "refund_rate": 25.0,
    }
    data_quality = analysis["data_quality"]
    assert data_quality["row_count"] == 5
    assert data_quality["duplicate_row_count"] == 1
    assert data_quality["duplicate_order_id_count"] == 1
    assert data_quality["missing_value_summary"] == {"discount": 2, "gender": 1}
    assert data_quality["invalid_date_count"] == 1
    assert data_quality["invalid_unit_price_count"] == 1
    assert data_quality["zero_unit_price_count"] == 1
    assert data_quality["zero_quantity_count"] == 1
    assert data_quality["invalid_quantity_count"] == 0
    assert data_quality["invalid_discount_count"] == 0
    assert data_quality["invalid_age_count"] == 2
    assert data_quality["invalid_status_count"] == 0
    assert data_quality["amount_mismatch_count"] == 1


def test_order_analyzer_keeps_real_zero_and_skips_missing_discount_rows() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3"],
            "unit_price": [0, 10, 10],
            "quantity": [2, 2, -1],
            "discount": [1, None, 1.2],
            "sales_amount": [0, None, None],
        }
    )

    analysis = OrderAnalyzer().analyze(frame, _plan(frame))

    assert analysis["overview"]["sales_total"] == 0.0
    assert analysis["overview"]["valid_sales_order_count"] == 1
    assert analysis["data_quality"]["invalid_quantity_count"] == 1
    assert analysis["data_quality"]["invalid_discount_count"] == 1


def test_order_analyzer_uses_unique_order_ids_for_repeat_customers() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["O-1", "O-1", "O-2", "O-3"],
            "customer_id": ["U-1", "U-1", "U-1", "U-2"],
            "sales_amount": [20, 20, 30, 10],
        }
    )

    analysis = OrderAnalyzer().analyze(frame, _plan(frame))

    assert analysis["overview"]["order_count"] == 3
    assert analysis["customer_analysis"] == {
        "unique_customer_count": 2,
        "repeat_customer_count": 1,
        "repeat_customer_rate": 50.0,
        "average_orders_per_customer": 1.5,
        "top_customers": [
            {"customer_id": "U-1", "order_count": 2, "sales_amount": 50.0},
            {"customer_id": "U-2", "order_count": 1, "sales_amount": 10.0},
        ],
    }
