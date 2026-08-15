from __future__ import annotations

import pandas as pd

from app.analysis_modules.generic import GenericModule
from app.analysis_modules.order import OrderModule
from app.analysis_modules.registry import ModuleRegistry
from app.analysis_modules.student_score import StudentScoreModule
from app.services.analysis_planner import AnalysisPlanner


def build_default_registry() -> ModuleRegistry:
    """Build the deterministic registry used by the analysis orchestration layer."""
    return ModuleRegistry(
        [
            OrderModule(),
            StudentScoreModule(),
            GenericModule(),
        ]
    )


class AnalysisEngine:
    """Create a domain selection and capability plan without calculating domain metrics."""

    def __init__(
        self,
        registry: ModuleRegistry | None = None,
        planner: AnalysisPlanner | None = None,
    ) -> None:
        self._registry = registry or build_default_registry()
        self._planner = planner or AnalysisPlanner()

    def build_context(self, frame: pd.DataFrame) -> dict[str, object]:
        available_set = self._planner.available_fields_from_dataframe(frame)
        available_fields = [
            str(column) for column in frame.columns if str(column) in available_set
        ]
        # Domain identity comes from the cleaned table schema, while execution
        # support still requires a real non-null value through ``available_set``.
        selected_module = self._registry.select_module(
            {str(column) for column in frame.columns}
        )
        analysis_plan = self._planner.plan(
            available_set,
            selected_module.capabilities(),
        )
        return {
            "selected_module": {
                "id": selected_module.id,
                "name": selected_module.name,
            },
            "available_fields": available_fields,
            "analysis_plan": analysis_plan,
        }

    @staticmethod
    def build_generic_analysis(frame: pd.DataFrame) -> dict[str, object]:
        """Return only schema and missing-value facts for generic tables."""
        row_count = len(frame.index)
        column_profile = [
            {
                "name": str(column),
                "dtype": str(frame[column].dtype),
                "non_null_count": int(frame[column].notna().sum()),
                "null_count": int(frame[column].isna().sum()),
            }
            for column in frame.columns
        ]
        missing_value_analysis = [
            {
                "column": item["name"],
                "missing_count": item["null_count"],
                "missing_rate": round(item["null_count"] / row_count * 100, 2)
                if row_count
                else 0.0,
            }
            for item in column_profile
        ]
        return {
            "row_count": row_count,
            "column_profile": column_profile,
            "missing_value_analysis": missing_value_analysis,
        }
