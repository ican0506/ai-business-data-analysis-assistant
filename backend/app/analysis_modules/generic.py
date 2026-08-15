from __future__ import annotations

from collections.abc import Sequence

from app.analysis_modules.base import AnalysisCapability, AnalysisModule


GENERIC_ANALYSIS_CAPABILITIES: tuple[AnalysisCapability, ...] = (
    AnalysisCapability(id="row_count", name="行数统计"),
    AnalysisCapability(id="column_profile", name="列信息概览"),
    AnalysisCapability(id="missing_value_analysis", name="缺失值分析"),
)

GENERIC_TYPE_DEPENDENT_CAPABILITIES: tuple[AnalysisCapability, ...] = (
    AnalysisCapability(
        id="numeric_summary",
        name="数值列统计",
        description="需要至少一个可用数值列。",
    ),
    AnalysisCapability(
        id="categorical_summary",
        name="分类列统计",
        description="需要至少一个可用分类列。",
    ),
    AnalysisCapability(
        id="datetime_summary",
        name="日期列统计",
        description="需要至少一个可用日期列。",
    ),
)


class GenericModule(AnalysisModule):
    """Fallback module for tables without reliable domain signals."""

    id = "generic"
    name = "通用表格分析"
    is_fallback = True

    def capabilities(self) -> Sequence[AnalysisCapability]:
        return GENERIC_ANALYSIS_CAPABILITIES

    def type_dependent_capabilities(self) -> Sequence[AnalysisCapability]:
        """Expose metadata for future dtype-aware planning without changing Planner."""
        return GENERIC_TYPE_DEPENDENT_CAPABILITIES

    def match_score(self, available_fields: set[str]) -> float:
        return 0.0
