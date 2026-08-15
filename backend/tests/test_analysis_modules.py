from collections.abc import Sequence

from app.analysis_modules.base import AnalysisCapability, AnalysisModule
from app.analysis_modules.generic import GenericModule
from app.analysis_modules.order import ORDER_ANALYSIS_CAPABILITIES, OrderModule
from app.analysis_modules.registry import ModuleRegistry
from app.analysis_modules.student_score import StudentScoreModule
from app.services.analysis_planner import (
    AnalysisPlanner,
    ORDER_ANALYSIS_CAPABILITIES as COMPATIBLE_ORDER_ANALYSIS_CAPABILITIES,
)


def test_order_module_reuses_all_existing_order_capabilities() -> None:
    module = OrderModule()

    assert module.capabilities() is ORDER_ANALYSIS_CAPABILITIES
    assert {
        "order_count",
        "product_quantity",
        "sales_total",
        "region_sales",
        "sales_trend",
        "customer_analysis",
        "refund_analysis",
        "target_completion",
    } == {capability.id for capability in module.capabilities()}
    assert COMPATIBLE_ORDER_ANALYSIS_CAPABILITIES is ORDER_ANALYSIS_CAPABILITIES


def test_student_score_module_plans_only_supported_capabilities() -> None:
    module = StudentScoreModule()
    results = {
        item["id"]: item
        for item in AnalysisPlanner().plan(
            {"student_id", "score"}, module.capabilities()
        )
    }

    assert results["student_count"]["supported"] is True
    assert results["score_summary"]["supported"] is True
    assert results["student_score"]["supported"] is True
    assert results["subject_score"]["supported"] is False
    assert results["class_score"]["supported"] is False
    assert results["exam_trend"]["supported"] is False


def test_student_score_module_supports_all_declared_field_combinations() -> None:
    module = StudentScoreModule()
    results = {
        item["id"]: item
        for item in AnalysisPlanner().plan(
            {"student_id", "student_name", "subject", "score", "class_name", "exam_date"},
            module.capabilities(),
        )
    }

    assert all(item["supported"] is True for item in results.values())


def test_registry_selects_order_for_reliable_order_signals() -> None:
    registry = ModuleRegistry([OrderModule(), StudentScoreModule(), GenericModule()])

    selected = registry.select_module({"order_id", "product", "quantity", "unit_price"})

    assert selected.id == "order"


def test_registry_selects_student_score_for_reliable_score_signals() -> None:
    registry = ModuleRegistry([OrderModule(), StudentScoreModule(), GenericModule()])

    selected = registry.select_module({"student_id", "student_name", "subject", "score"})

    assert selected.id == "student_score"


def test_registry_uses_generic_for_unknown_or_weak_domain_signals() -> None:
    registry = ModuleRegistry([OrderModule(), StudentScoreModule(), GenericModule()])

    assert registry.select_module({"temperature", "city", "timestamp"}).id == "generic"
    assert registry.select_module({"date", "status"}).id == "generic"
    assert registry.select_module(set()).id == "generic"


def test_registry_uses_registration_order_to_break_matching_score_ties() -> None:
    class StaticModule(AnalysisModule):
        def __init__(self, module_id: str) -> None:
            self.id = module_id
            self.name = module_id

        def capabilities(self) -> Sequence[AnalysisCapability]:
            return ()

        def match_score(self, available_fields: set[str]) -> float:
            return 0.6 if "signal" in available_fields else 0.0

    first = StaticModule("first")
    second = StaticModule("second")
    registry = ModuleRegistry([first, second, GenericModule()])

    assert registry.select_module({"signal"}) is first


def test_registry_falls_back_when_best_score_is_below_threshold() -> None:
    class WeakModule(AnalysisModule):
        id = "weak"
        name = "weak"

        def capabilities(self) -> Sequence[AnalysisCapability]:
            return ()

        def match_score(self, available_fields: set[str]) -> float:
            return 0.49

    registry = ModuleRegistry([WeakModule(), GenericModule()], minimum_domain_score=0.5)

    assert registry.select_module({"signal"}).id == "generic"


def test_generic_module_keeps_type_dependent_capabilities_out_of_field_planner() -> None:
    module = GenericModule()

    assert {capability.id for capability in module.capabilities()} == {
        "row_count",
        "column_profile",
        "missing_value_analysis",
    }
    assert {capability.id for capability in module.type_dependent_capabilities()} == {
        "numeric_summary",
        "categorical_summary",
        "datetime_summary",
    }
