from __future__ import annotations

from collections.abc import Sequence

from app.analysis_modules.base import AnalysisCapability, AnalysisModule


INVENTORY_ANALYSIS_CAPABILITIES: tuple[AnalysisCapability, ...] = (
    AnalysisCapability(
        id="inventory_count",
        name="库存商品数量",
        any_of=(("product_id",), ("product_name",)),
    ),
    AnalysisCapability(id="stock_summary", name="库存概览", all_of=("stock_quantity",)),
    AnalysisCapability(
        id="low_stock_analysis",
        name="低库存分析",
        all_of=("stock_quantity", "safety_stock"),
    ),
    AnalysisCapability(
        id="inventory_value",
        name="库存价值分析",
        all_of=("stock_quantity", "unit_cost"),
    ),
    AnalysisCapability(
        id="category_stock",
        name="分类库存分析",
        all_of=("category", "stock_quantity"),
    ),
    AnalysisCapability(
        id="warehouse_stock",
        name="仓库库存分析",
        all_of=("warehouse", "stock_quantity"),
    ),
    AnalysisCapability(
        id="supplier_stock",
        name="供应商库存分析",
        all_of=("supplier", "stock_quantity"),
    ),
    AnalysisCapability(
        id="inventory_flow",
        name="库存流动分析",
        all_of=("inbound_quantity", "outbound_quantity"),
    ),
    AnalysisCapability(
        id="inventory_trend",
        name="库存趋势分析",
        all_of=("inventory_date", "stock_quantity"),
    ),
)


class InventoryModule(AnalysisModule):
    """Recognize inventory tables only from reliable field combinations."""

    id = "inventory"
    name = "库存分析"

    _SIGNALS: tuple[frozenset[str], ...] = (
        frozenset(("product_id", "stock_quantity")),
        frozenset(("product_name", "stock_quantity")),
        frozenset(("warehouse", "stock_quantity")),
        frozenset(("stock_quantity", "safety_stock")),
        frozenset(("stock_quantity", "unit_cost")),
    )

    def capabilities(self) -> Sequence[AnalysisCapability]:
        return INVENTORY_ANALYSIS_CAPABILITIES

    def match_score(self, available_fields: set[str]) -> float:
        matched_signal_count = sum(signal <= available_fields for signal in self._SIGNALS)
        if not matched_signal_count:
            return 0.0
        return min(1.0, 0.6 + (matched_signal_count - 1) * 0.1)
