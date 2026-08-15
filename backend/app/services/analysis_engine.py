from __future__ import annotations

import pandas as pd

from app.analysis_modules.generic import GenericModule
from app.analysis_modules.order import OrderModule
from app.analysis_modules.registry import ModuleRegistry
from app.analysis_modules.student_score import StudentScoreModule
from app.services.canonical_field_mapper import CanonicalFieldMapper
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
        field_mapper: CanonicalFieldMapper | None = None,
    ) -> None:
        self._registry = registry or build_default_registry()
        self._planner = planner or AnalysisPlanner()
        self._field_mapper = field_mapper or CanonicalFieldMapper()

    def build_context(self, frame: pd.DataFrame) -> dict[str, object]:
        """Return public analysis context without exposing the analysis DataFrame."""
        _mapped_frame, context = self.prepare_context(frame)
        return context

    def prepare_context(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
        """Create the one mapped frame shared by all later analysis steps."""
        mapped_frame, field_mapping = self._field_mapper.map_dataframe(frame)
        available_set = self._planner.available_fields_from_dataframe(mapped_frame)
        available_fields = [
            str(column) for column in mapped_frame.columns if str(column) in available_set
        ]
        # Module identity is determined from the mapped schema.  Individual
        # capabilities still require non-null values through ``available_set``.
        selected_module = self._registry.select_module(
            {str(column) for column in mapped_frame.columns}
        )
        analysis_plan = self._planner.plan(
            available_set,
            selected_module.capabilities(),
        )
        return mapped_frame, {
            "selected_module": {
                "id": selected_module.id,
                "name": selected_module.name,
            },
            "available_fields": available_fields,
            "analysis_plan": analysis_plan,
            "field_mapping": field_mapping,
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
