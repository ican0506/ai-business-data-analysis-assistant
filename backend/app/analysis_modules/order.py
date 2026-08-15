from __future__ import annotations

from collections.abc import Sequence

from app.analysis_modules.base import AnalysisCapability, AnalysisModule


ORDER_ANALYSIS_CAPABILITIES: tuple[AnalysisCapability, ...] = (
    AnalysisCapability(id="order_count", name="订单数量分析", all_of=("order_id",)),
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
    AnalysisCapability(id="customer_analysis", name="客户分析", all_of=("customer_id",)),
    AnalysisCapability(id="refund_analysis", name="退款分析", all_of=("status",)),
)


class OrderModule(AnalysisModule):
    id = "order"
    name = "订单分析"

    _SIGNALS: tuple[frozenset[str], ...] = (
        frozenset(("order_id", "product")),
        frozenset(("sales_amount", "product")),
        frozenset(("quantity", "unit_price")),
        frozenset(("customer_id", "order_id")),
    )

    def capabilities(self) -> Sequence[AnalysisCapability]:
        return ORDER_ANALYSIS_CAPABILITIES

    def match_score(self, available_fields: set[str]) -> float:
        matched_signal_count = sum(
            signal <= available_fields for signal in self._SIGNALS
        )
        if not matched_signal_count:
            return 0.0
        return min(1.0, 0.55 + (matched_signal_count - 1) * 0.15)
