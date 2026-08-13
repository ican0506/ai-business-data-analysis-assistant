from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AnalysisCapability:
    id: str
    name: str
    all_of: tuple[str, ...] = ()
    any_of: tuple[tuple[str, ...], ...] = ()
    description: str | None = None


class AnalysisPlanner:
    """Plan analysis capabilities from a set of available, cleaned fields."""

    @staticmethod
    def available_fields_from_dataframe(dataframe: pd.DataFrame) -> set[str]:
        """Return columns that contain at least one non-pandas-missing value."""
        return {
            str(column)
            for index, column in enumerate(dataframe.columns)
            if dataframe.iloc[:, index].notna().any()
        }

    def plan(
        self,
        available_fields: set[str],
        capabilities: Sequence[AnalysisCapability],
    ) -> list[dict[str, object]]:
        available = {str(field) for field in available_fields}
        return [self._plan_capability(available, capability) for capability in capabilities]

    def _plan_capability(
        self,
        available_fields: set[str],
        capability: AnalysisCapability,
    ) -> dict[str, object]:
        all_of_missing = self._missing_fields(capability.all_of, available_fields)
        matched_any_of: tuple[str, ...] | None = None
        any_of_missing: list[str] = []

        if capability.any_of:
            candidates = [
                self._missing_fields(candidate, available_fields)
                for candidate in capability.any_of
            ]
            for index, missing_fields in enumerate(candidates):
                if not missing_fields:
                    matched_any_of = capability.any_of[index]
                    break
            else:
                any_of_missing = min(candidates, key=len)

        missing_fields = self._unique_fields(all_of_missing + any_of_missing)
        supported = not missing_fields
        result: dict[str, object] = {
            "id": capability.id,
            "name": capability.name,
            "supported": supported,
            "missing_fields": missing_fields,
            "reason": None if supported else "缺少所需字段",
        }

        if supported:
            result["matched_fields"] = self._unique_fields(
                list(capability.all_of) + list(matched_any_of or ())
            )

        return result

    @staticmethod
    def _missing_fields(required_fields: tuple[str, ...], available_fields: set[str]) -> list[str]:
        return [field for field in required_fields if field not in available_fields]

    @staticmethod
    def _unique_fields(fields: list[str]) -> list[str]:
        return list(dict.fromkeys(fields))


ORDER_ANALYSIS_CAPABILITIES: tuple[AnalysisCapability, ...] = (
    AnalysisCapability(
        id="order_count",
        name="订单数量分析",
        all_of=("order_id",),
    ),
    AnalysisCapability(
        id="product_quantity",
        name="商品销量分析",
        all_of=("product", "quantity"),
    ),
    AnalysisCapability(
        id="sales_total",
        name="销售额分析",
        any_of=(("sales_amount",), ("unit_price", "quantity")),
    ),
    AnalysisCapability(
        id="region_sales",
        name="区域销售分析",
        all_of=("region",),
        any_of=(("sales_amount",), ("unit_price", "quantity")),
    ),
    AnalysisCapability(
        id="sales_trend",
        name="销售趋势分析",
        all_of=("date",),
        any_of=(("sales_amount",), ("unit_price", "quantity")),
    ),
    AnalysisCapability(
        id="target_completion",
        name="目标完成率分析",
        all_of=("target_amount",),
        any_of=(("sales_amount",), ("unit_price", "quantity")),
    ),
    AnalysisCapability(
        id="customer_analysis",
        name="客户分析",
        all_of=("customer_id",),
    ),
    AnalysisCapability(
        id="refund_analysis",
        name="退款分析",
        all_of=("status",),
    ),
)
