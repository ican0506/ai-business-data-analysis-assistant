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
            {"source": "学号", "target": "student_id"},
            {"source": "姓名", "target": "student_name"},
            {"source": "科目", "target": "subject"},
            {"source": "成绩", "target": "score"},
            {"source": "班级", "target": "class_name"},
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
