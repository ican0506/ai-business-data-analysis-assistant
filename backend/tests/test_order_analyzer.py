from __future__ import annotations

import pandas as pd

from app.analysis_modules.order import ORDER_ANALYSIS_CAPABILITIES
from app.analysis_modules.order import OrderModule
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
    assert overview["verified_sales_total"] == 180.0
    assert overview["sales_total"] == 180.0
    assert overview["verified_order_count"] == 2
    assert overview["average_verified_order_value"] == 90.0
    assert overview["average_order_value"] == 90.0
    assert overview["amount_mismatch_count"] == 1
    assert overview["amount_mismatch_rate"] == 50.0
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
    assert data_quality["amount_comparable_count"] == 2
    assert data_quality["unverified_order_count"] == 2
    assert data_quality["unverified_amount_total"] == 100.0


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
                "unit_price": [20, 20, 30, 10],
                "quantity": [1, 1, 1, 1],
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


def test_order_analyzer_normalizes_chinese_dates_and_counts_only_nonempty_invalid_dates() -> None:
    frame = pd.DataFrame({
        "order_id": [f"O-{index}" for index in range(10)],
        "unit_price": [10] * 10,
        "quantity": [1] * 10,
        "date": [
            "2026-01-08", "2026/01/08", "2026.01.08", "2026-01-08 09:45",
            "2026/01/08 09:45", "2026年01月08日", "2026年01月08日 09:45",
            "2026年1月8日 9:45", "not-a-date", None,
        ],
    })

    analysis = OrderAnalyzer().analyze(frame, _plan(frame))

    assert analysis["data_quality"]["invalid_date_count"] == 1
    assert OrderAnalyzer._parse_order_dates(frame["date"]).notna().sum() == 8


def test_order_analyzer_standardizes_known_regions_and_keeps_unknown_regions() -> None:
    frame = pd.DataFrame({
        "order_id": ["O-1", "O-2", "O-3", "O-4", "O-5"],
        "region": [" 郑州市 ", "zhengzhou", "南阳市", " NANYANG ", "自定义地区"],
        "unit_price": [10, 20, 30, 40, 50],
        "quantity": [1, 1, 1, 1, 1],
    })

    analysis = OrderAnalyzer().analyze(frame, _plan(frame))

    assert [(item["name"], item["region_sales"]) for item in analysis["region_analysis"]] == [
        ("南阳", 70.0), ("自定义地区", 50.0), ("郑州", 30.0),
    ]


def test_order_analyzer_standardizes_xuchang_and_does_not_guess_unknown_region() -> None:
    frame = pd.DataFrame({
        "order_id": ["O-1", "O-2", "O-3", "O-4"],
        "region": ["许昌", "许昌市", "xuchang", "未知城市ABC"],
        "unit_price": [10, 10, 10, 20],
        "quantity": [1, 1, 1, 1],
    })

    regions = OrderAnalyzer().analyze(frame, _plan(frame))["region_analysis"]

    assert [(item["name"], item["region_sales"]) for item in regions] == [("许昌", 30.0), ("未知城市ABC", 20.0)]


def test_order_analyzer_calculates_aggregate_contact_quality_without_exposing_values() -> None:
    frame = pd.DataFrame({
        "order_id": ["O-1", "O-2", "O-3", "O-4"],
        "phone": ["+86 138-0000-0000", "123", None, "abc"],
        "email": ["valid@example.com", "bad-email", None, "also.valid@example.cn"],
    })

    analysis = OrderAnalyzer().analyze(frame, _plan(frame))
    quality = analysis["data_quality"]

    assert quality["phone_present_count"] == 3
    assert quality["phone_missing_count"] == 1
    assert quality["phone_valid_count"] == 1
    assert quality["phone_invalid_count"] == 2
    assert quality["email_present_count"] == 3
    assert quality["email_missing_count"] == 1
    assert quality["email_valid_count"] == 2
    assert quality["email_invalid_count"] == 1
    assert quality["contact_complete_count"] == 1
    assert quality["contact_complete_rate"] == 25.0
    assert "13800000000" not in str(analysis)


def test_phone_and_email_only_do_not_identify_an_order_dataset() -> None:
    assert OrderModule().match_score({"customer_name", "phone", "email"}) == 0.0


def test_order_analyzer_excludes_unverifiable_and_conflicting_raw_amounts_from_verified_sales() -> None:
    frame = pd.DataFrame({
        "order_id": ["O-1", "O-2", "O-3", "O-4"],
        "product": ["A", "A", "B", "C"],
        "customer_id": ["U-1", "U-2", "U-3", "U-4"],
        "unit_price": [100, 100, None, 100],
        "quantity": [2, 2, 2, 2],
        "discount": [0.8, 0.8, 0.8, None],
        "sales_amount": [160, 999999.99, 999999.99, 180],
    })

    analysis = OrderAnalyzer().analyze(frame, _plan(frame))
    overview = analysis["overview"]
    quality = analysis["data_quality"]

    assert overview["verified_sales_total"] == 320.0
    assert overview["sales_total"] == 320.0
    assert overview["verified_order_count"] == 2
    assert overview["average_verified_order_value"] == 160.0
    assert overview["average_order_value"] == 160.0
    assert quality["unverified_amount_count"] == 2
    assert quality["unverified_order_count"] == 2
    assert quality["unverified_amount_total"] == 1000179.99
    assert quality["amount_mismatch_count"] == 1
    assert quality["amount_comparable_count"] == 2
    assert quality["amount_mismatch_rate"] == 50.0
    assert next(item for item in analysis["product_analysis"] if item["name"] == "B")["sales_amount"] is None
    assert all(item["sales_amount"] != 999999.99 for item in analysis["customer_analysis"]["top_customers"])


def test_order_analyzer_uses_verified_order_level_amount_for_multi_line_orders_and_removes_exact_duplicates() -> None:
    frame = pd.DataFrame({
        "order_id": ["O-1", "O-1", "O-1", "O-2"],
        "product": ["A", "B", "A", "C"],
        "unit_price": [100, 50, 100, 100],
        "quantity": [2, 1, 2, 1],
    })

    analysis = OrderAnalyzer().analyze(frame, _plan(frame))
    overview = analysis["overview"]

    assert overview["order_count"] == 2
    assert overview["verified_sales_total"] == 350.0
    assert overview["verified_order_count"] == 2
    assert overview["average_verified_order_value"] == 175.0
    assert overview["maximum_verified_order_value"] == 250.0
    assert overview["minimum_verified_order_value"] == 100.0
    assert analysis["data_quality"]["duplicate_row_count"] == 1


def test_order_analyzer_verifies_price_times_quantity_when_discount_column_is_absent() -> None:
    frame = pd.DataFrame({"order_id": ["O-1"], "unit_price": [100], "quantity": [2]})

    analysis = OrderAnalyzer().analyze(frame, _plan(frame))

    assert analysis["overview"]["verified_sales_total"] == 200.0
    assert analysis["data_quality"]["unverified_order_count"] == 0
