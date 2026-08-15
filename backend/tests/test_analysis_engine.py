from __future__ import annotations

import pandas as pd

from app.services.analysis_engine import AnalysisEngine, build_default_registry


def plan_by_id(context: dict) -> dict[str, dict]:
    return {item["id"]: item for item in context["analysis_plan"]}


def test_engine_selects_order_module_and_plans_derived_sales() -> None:
    context = AnalysisEngine().build_context(
        pd.DataFrame(
            {
                "order_id": ["O-1"],
                "product": ["A"],
                "quantity": [2],
                "unit_price": [10],
            }
        )
    )

    assert context["selected_module"] == {"id": "order", "name": "订单分析"}
    assert plan_by_id(context)["sales_total"]["matched_fields"] == [
        "unit_price",
        "quantity",
    ]


def test_engine_selects_student_score_and_only_plans_score_capabilities() -> None:
    context = AnalysisEngine().build_context(
        pd.DataFrame(
            {"student_id": ["S-1"], "subject": ["math"], "score": [95]}
        )
    )

    plan = plan_by_id(context)
    assert context["selected_module"]["id"] == "student_score"
    assert plan["student_count"]["supported"] is True
    assert plan["score_summary"]["supported"] is True
    assert plan["subject_score"]["supported"] is True
    assert plan["student_score"]["supported"] is True
    assert plan["class_score"]["supported"] is False
    assert plan["exam_trend"]["supported"] is False


def test_engine_uses_generic_module_for_unknown_and_empty_dataframes() -> None:
    engine = AnalysisEngine()

    unknown = engine.build_context(
        pd.DataFrame({"city": ["Shanghai"], "temperature": [30]})
    )
    empty = engine.build_context(pd.DataFrame())

    assert unknown["selected_module"]["id"] == "generic"
    assert empty["selected_module"]["id"] == "generic"
    assert empty["available_fields"] == []


def test_default_registry_registers_each_module_once() -> None:
    registry = build_default_registry()

    assert registry.select_module({"order_id", "product"}).id == "order"
    assert registry.select_module({"student_id", "score"}).id == "student_score"
    assert registry.select_module(set()).id == "generic"


def test_engine_maps_chinese_student_headers_before_selecting_module_and_planning() -> None:
    context = AnalysisEngine().build_context(
        pd.DataFrame(
            {
                "学号": ["001"],
                "姓名": ["张三"],
                "科目": ["数学"],
                "成绩": [90],
                "班级": ["一班"],
            }
        )
    )

    assert context["selected_module"]["id"] == "student_score"
    assert context["available_fields"] == [
        "student_id",
        "student_name",
        "subject",
        "score",
        "class_name",
    ]
    assert plan_by_id(context)["class_score"]["supported"] is True
    assert context["field_mapping"]["mappings"][0] == {
        "source": "学号",
        "target": "student_id",
        "method": "automatic",
    }


def test_engine_keeps_all_empty_mapped_score_unavailable() -> None:
    context = AnalysisEngine().build_context(
        pd.DataFrame({"学号": ["001"], "成绩": [None]})
    )

    assert context["selected_module"]["id"] == "student_score"
    assert "score" not in context["available_fields"]
    assert plan_by_id(context)["score_summary"]["supported"] is False
