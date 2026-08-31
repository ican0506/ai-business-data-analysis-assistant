"""Execute a safe, structured order-data query with existing analysis rules."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta

import pandas as pd

from app.schemas.data_chat import (
    DataChatGroupBy,
    DataChatMetric,
    DataChatQueryPlan,
    DataChatSortDirection,
)
from app.services.analysis_engine import AnalysisEngine
from app.services.order_analyzer import OrderAnalyzer


class MetricQueryEngine:
    """Pure-Python executor for validated ``DataChatQueryPlan`` instances."""

    _METRIC_CAPABILITIES = {
        DataChatMetric.SALES_AMOUNT: "sales_total",
        DataChatMetric.ORDER_COUNT: "order_count",
    }

    def __init__(
        self,
        analysis_engine: AnalysisEngine | None = None,
        order_analyzer: OrderAnalyzer | None = None,
    ) -> None:
        self._analysis_engine = analysis_engine or AnalysisEngine()
        self._order_analyzer = order_analyzer or OrderAnalyzer()

    def query(
        self,
        dataframe: pd.DataFrame,
        query_plan: DataChatQueryPlan,
        field_overrides: Mapping[str, str] | None = None,
    ) -> dict[str, object]:
        """Run a whitelist-validated order query without dynamic execution."""
        frame, context = self._analysis_engine.prepare_context(
            dataframe, field_overrides=field_overrides
        )
        if context["selected_module"]["id"] != "order":
            return self._unsupported_domain_result(query_plan, context)

        analysis_plan = context["analysis_plan"]
        plan_by_id = {str(item["id"]): item for item in analysis_plan}
        prepared, _quality, _order_level = self._order_analyzer._prepare(frame)
        filtered_index = self._filtered_index(prepared, query_plan)
        filtered_frame = frame.loc[filtered_index].copy()
        filtered_prepared, _quality, _order_level = self._order_analyzer._prepare(filtered_frame)
        order_analysis = self._order_analyzer.analyze(filtered_frame, analysis_plan)

        unavailable = self._unavailable_metrics(
            query_plan.metrics, plan_by_id, filtered_prepared, order_analysis
        )
        unavailable.extend(
            self._unavailable_scope(query_plan, set(context["available_fields"]))
        )
        unavailable_names = {item["metric"] for item in unavailable}
        available_metrics = [
            metric for metric in query_plan.metrics if metric.value not in unavailable_names
        ]

        if query_plan.group_by:
            rows = self._group_rows(
                query_plan,
                frame,
                filtered_prepared,
                analysis_plan,
                order_analysis,
                available_metrics,
            )
            rows = self._sort_and_limit_rows(rows, query_plan)
            metrics: dict[str, object] = {}
        else:
            metrics = self._global_metrics(order_analysis, filtered_prepared, available_metrics)
            rows = []

        status = "success" if not unavailable else ("partial" if metrics or rows else "unavailable")
        return {
            "status": status,
            "domain": "order",
            "metrics": metrics,
            "group_by": [item.value for item in query_plan.group_by],
            "rows": rows,
            "unavailable": unavailable,
            "data_scope": {
                "date_range": self._date_range_payload(query_plan),
                "filters": query_plan.filters.model_dump(),
                "row_count": int(len(filtered_frame.index)),
            },
            "analysis_context": {
                "selected_module": context["selected_module"],
                "available_fields": context["available_fields"],
            },
        }

    def _unsupported_domain_result(
        self, query_plan: DataChatQueryPlan, context: dict[str, object]
    ) -> dict[str, object]:
        return {
            "status": "unavailable",
            "domain": "order",
            "metrics": {},
            "group_by": [item.value for item in query_plan.group_by],
            "rows": [],
            "unavailable": [
                {"metric": metric.value, "reason": "当前数据集不是 Order 订单领域"}
                for metric in query_plan.metrics
            ],
            "data_scope": {
                "date_range": self._date_range_payload(query_plan),
                "filters": query_plan.filters.model_dump(),
                "row_count": 0,
            },
            "analysis_context": {
                "selected_module": context["selected_module"],
                "available_fields": context["available_fields"],
            },
        }

    def _filtered_index(
        self, prepared: pd.DataFrame, query_plan: DataChatQueryPlan
    ) -> pd.Index:
        mask = pd.Series(True, index=prepared.index)
        if query_plan.date_range is not None:
            start = pd.Timestamp(query_plan.date_range.start)
            end_exclusive = pd.Timestamp(query_plan.date_range.end + timedelta(days=1))
            mask &= prepared["_date"].ge(start) & prepared["_date"].lt(end_exclusive)
        if query_plan.filters.region is not None:
            expected_region = self._order_analyzer._normalize_region(query_plan.filters.region)
            mask &= prepared["_region"].eq(expected_region)
        if query_plan.filters.product is not None:
            mask &= prepared["_product"].eq(query_plan.filters.product.strip())
        if query_plan.filters.category is not None:
            mask &= prepared["_category"].eq(query_plan.filters.category.strip())
        return prepared.index[mask.fillna(False)]

    def _unavailable_metrics(
        self,
        metrics: list[DataChatMetric],
        plan_by_id: dict[str, object],
        prepared: pd.DataFrame,
        order_analysis: dict[str, object],
    ) -> list[dict[str, str]]:
        unavailable: list[dict[str, str]] = []
        overview = order_analysis["overview"]
        for metric in metrics:
            capability = self._METRIC_CAPABILITIES.get(metric)
            if capability is not None and not self._is_supported(plan_by_id, capability):
                unavailable.append({"metric": metric.value, "reason": f"{capability} 字段不可用于计算"})
                continue
            if metric is DataChatMetric.SALES_QUANTITY:
                if self._valid_quantities(prepared).empty:
                    unavailable.append({"metric": metric.value, "reason": "quantity 字段不可用于计算"})
            elif metric is DataChatMetric.SALES_AMOUNT and overview["sales_total"] is None:
                unavailable.append({"metric": metric.value, "reason": "没有可验证的销售金额"})
            elif metric is DataChatMetric.AVERAGE_ORDER_VALUE and overview["average_order_value"] is None:
                unavailable.append({"metric": metric.value, "reason": "没有可验证的订单金额"})
        return unavailable

    @staticmethod
    def _unavailable_scope(
        query_plan: DataChatQueryPlan, available_fields: set[object]
    ) -> list[dict[str, str]]:
        required_field: str | None = None
        if query_plan.date_range is not None:
            required_field = "date"
        if query_plan.group_by:
            group_field = query_plan.group_by[0].value
            required_field = "date" if group_field == DataChatGroupBy.MONTH.value else group_field
        if required_field is None or required_field in available_fields:
            return []
        suffix = "用于分组" if query_plan.group_by else "用于日期筛选"
        return [
            {"metric": metric.value, "reason": f"{required_field} 字段不可{suffix}"}
            for metric in query_plan.metrics
        ]

    def _global_metrics(
        self,
        order_analysis: dict[str, object],
        prepared: pd.DataFrame,
        metrics: list[DataChatMetric],
    ) -> dict[str, object]:
        overview = order_analysis["overview"]
        result: dict[str, object] = {}
        for metric in metrics:
            if metric is DataChatMetric.SALES_AMOUNT:
                result[metric.value] = overview["sales_total"]
            elif metric is DataChatMetric.SALES_QUANTITY:
                result[metric.value] = self._round(self._valid_quantities(prepared).sum())
            elif metric is DataChatMetric.ORDER_COUNT:
                result[metric.value] = overview["order_count"]
            elif metric is DataChatMetric.AVERAGE_ORDER_VALUE:
                result[metric.value] = overview["average_order_value"]
        return result

    def _group_rows(
        self,
        query_plan: DataChatQueryPlan,
        original_frame: pd.DataFrame,
        prepared: pd.DataFrame,
        analysis_plan: list[dict[str, object]],
        order_analysis: dict[str, object],
        metrics: list[DataChatMetric],
    ) -> list[dict[str, object]]:
        group_by = query_plan.group_by[0]
        if group_by is DataChatGroupBy.PRODUCT:
            return self._dimension_rows(order_analysis["product_analysis"], "product", metrics)
        if group_by is DataChatGroupBy.CATEGORY:
            return self._dimension_rows(order_analysis["category_analysis"], "category", metrics)
        if group_by is DataChatGroupBy.REGION:
            return self._dimension_rows(order_analysis["region_analysis"], "region", metrics)
        return self._month_rows(original_frame, prepared, analysis_plan, metrics)

    @staticmethod
    def _dimension_rows(
        items: list[dict[str, object]],
        dimension: str,
        metrics: list[DataChatMetric],
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for item in items:
            label = item.get("category") if dimension == "category" else item.get("name")
            row: dict[str, object] = {dimension: label}
            for metric in metrics:
                if metric is DataChatMetric.SALES_AMOUNT:
                    row[metric.value] = item.get("sales_amount") if dimension != "region" else item.get("region_sales")
                elif metric is DataChatMetric.SALES_QUANTITY:
                    row[metric.value] = item.get("quantity") if dimension != "region" else item.get("region_quantity")
                elif metric is DataChatMetric.ORDER_COUNT:
                    row[metric.value] = item.get("order_count") if dimension != "region" else item.get("region_order_count")
            rows.append(row)
        return rows

    def _month_rows(
        self,
        original_frame: pd.DataFrame,
        prepared: pd.DataFrame,
        analysis_plan: list[dict[str, object]],
        metrics: list[DataChatMetric],
    ) -> list[dict[str, object]]:
        dated = prepared.dropna(subset=["_date"]).copy()
        if dated.empty:
            return []
        dated["_month"] = dated["_date"].dt.to_period("M")
        rows: list[dict[str, object]] = []
        for month, group in dated.groupby("_month", sort=True):
            monthly_frame = original_frame.loc[group.index].copy()
            monthly_analysis = self._order_analyzer.analyze(monthly_frame, analysis_plan)
            monthly_prepared, _quality, _orders = self._order_analyzer._prepare(monthly_frame)
            values = self._global_metrics(monthly_analysis, monthly_prepared, metrics)
            rows.append({"month": str(month), **values})
        return rows

    @staticmethod
    def _valid_quantities(prepared: pd.DataFrame) -> pd.Series:
        rows = prepared.loc[~prepared["_duplicate_row"]]
        return rows["_quantity"].where(rows["_quantity"].ge(0)).dropna()

    @staticmethod
    def _is_supported(plan_by_id: dict[str, object], capability_id: str) -> bool:
        item = plan_by_id.get(capability_id)
        return bool(isinstance(item, dict) and item.get("supported"))

    @staticmethod
    def _round(value: object) -> float:
        return round(float(value), 2)

    @staticmethod
    def _date_range_payload(query_plan: DataChatQueryPlan) -> dict[str, str] | None:
        if query_plan.date_range is None:
            return None
        return {
            "start": query_plan.date_range.start.isoformat(),
            "end": query_plan.date_range.end.isoformat(),
        }

    @staticmethod
    def _sort_and_limit_rows(
        rows: list[dict[str, object]], query_plan: DataChatQueryPlan
    ) -> list[dict[str, object]]:
        if query_plan.group_by == [DataChatGroupBy.MONTH]:
            ordered = sorted(rows, key=lambda row: str(row["month"]))
        else:
            sort_metric = query_plan.sort.metric if query_plan.sort else query_plan.metrics[0]
            descending = query_plan.sort.direction is DataChatSortDirection.DESC if query_plan.sort else True
            dimension = query_plan.group_by[0].value
            ordered = sorted(
                rows,
                key=lambda row: (
                    -float(row.get(sort_metric.value) or 0) if descending else float(row.get(sort_metric.value) or 0),
                    str(row.get(dimension, "")),
                ),
            )
        return ordered[: query_plan.limit] if query_plan.limit is not None else ordered
