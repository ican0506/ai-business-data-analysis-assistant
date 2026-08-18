from __future__ import annotations

import pandas as pd

from app.services.canonical_field_mapper import CanonicalFieldMapper


def test_maps_complete_chinese_student_score_headers_without_mutating_source() -> None:
    frame = pd.DataFrame(
        {
            "学号": ["001"],
            "姓名": ["张三"],
            "科目": ["数学"],
            "成绩": [90],
            "班级": ["一班"],
            "备注": ["正常"],
        }
    )

    mapped, metadata = CanonicalFieldMapper().map_dataframe(frame)

    assert list(frame.columns) == ["学号", "姓名", "科目", "成绩", "班级", "备注"]
    assert list(mapped.columns) == [
        "student_id",
        "student_name",
        "subject",
        "score",
        "class_name",
        "备注",
    ]
    assert metadata == {
        "mappings": [
                {"source": "学号", "target": "student_id", "method": "automatic"},
                {"source": "姓名", "target": "student_name", "method": "automatic"},
                {"source": "科目", "target": "subject", "method": "automatic"},
                {"source": "成绩", "target": "score", "method": "automatic"},
                {"source": "班级", "target": "class_name", "method": "automatic"},
        ],
        "unmapped_columns": ["备注"],
        "conflicts": [],
    }


def test_maps_chinese_order_and_normalizes_english_header_variants() -> None:
    frame = pd.DataFrame(
        {
            "订单编号": ["O-1"],
            "商品名称": ["A"],
            "数量": [2],
            " Unit-Price ": [10],
            "区域": ["华东"],
        }
    )

    mapped, metadata = CanonicalFieldMapper().map_dataframe(frame)

    assert list(mapped.columns) == [
        "order_id",
        "product",
        "quantity",
        "unit_price",
        "region",
    ]
    assert metadata["conflicts"] == []


def test_maps_real_ecommerce_order_aliases_without_mapping_personal_contacts() -> None:
    frame = pd.DataFrame({
        "user_id": ["U-1"], "user_name": ["张三"], "city": ["郑州市"],
        "order_amount": [90], "order_status": ["已完成"], "order_time": ["2026-08-01"],
        "商品分类": ["数码"], "discount": [0.9], "payment_method": ["微信"],
        "phone": ["13800000000"], "email": ["demo@example.com"], "remark": ["仅质量检查"],
    })

    mapped, metadata = CanonicalFieldMapper().map_dataframe(frame)

    assert {"customer_id", "customer_name", "region", "sales_amount", "status", "date", "category", "discount", "payment_method"} <= set(mapped.columns)
    assert {"phone", "email", "remark"} <= set(mapped.columns)
    assert {"phone", "email", "remark"} <= set(metadata["unmapped_columns"])


def test_preserves_canonical_column_and_records_canonical_alias_conflict() -> None:
    frame = pd.DataFrame({"score": [90], "成绩": [99]})

    mapped, metadata = CanonicalFieldMapper().map_dataframe(frame)

    assert list(mapped.columns) == ["score", "成绩"]
    assert metadata["mappings"] == []
    assert metadata["unmapped_columns"] == []
    assert metadata["conflicts"] == [
        {
            "target": "score",
            "sources": ["score", "成绩"],
            "reason": "canonical field already exists",
        }
    ]


def test_preserves_multiple_aliases_and_records_conflict_without_mapping() -> None:
    frame = pd.DataFrame({"销售额": [100], "销售金额": [120]})

    mapped, metadata = CanonicalFieldMapper().map_dataframe(frame)

    assert list(mapped.columns) == ["销售额", "销售金额"]
    assert metadata["mappings"] == []
    assert metadata["unmapped_columns"] == []
    assert metadata["conflicts"] == [
        {
            "target": "sales_amount",
            "sources": ["销售额", "销售金额"],
            "reason": "multiple alias columns map to the same canonical field",
        }
    ]


def test_maps_all_empty_score_header_but_keeps_value_availability_for_planner() -> None:
    mapped, _metadata = CanonicalFieldMapper().map_dataframe(
        pd.DataFrame({"学号": ["001"], "成绩": [None]})
    )

    assert list(mapped.columns) == ["student_id", "score"]
    assert mapped["score"].isna().all()


def test_maps_chinese_inventory_headers_without_changing_order_product_mapping() -> None:
    inventory, inventory_metadata = CanonicalFieldMapper().map_dataframe(
        pd.DataFrame({"商品编号": ["P001"], "商品名称": ["商品A"], "库存数量": [5], "安全库存": [10], "单位成本": [20], "仓库": ["郑州仓"]})
    )
    order, _order_metadata = CanonicalFieldMapper().map_dataframe(
        pd.DataFrame({"订单编号": ["O001"], "商品名称": ["商品A"], "数量": [2], "单价": [5]})
    )

    assert list(inventory.columns) == ["product_id", "product_name", "stock_quantity", "safety_stock", "unit_cost", "warehouse"]
    assert list(order.columns) == ["order_id", "product", "quantity", "unit_price"]
    assert inventory_metadata["conflicts"] == []
