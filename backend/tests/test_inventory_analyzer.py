from __future__ import annotations

import pandas as pd

from app.analysis_modules.inventory import InventoryModule
from app.services.analysis_planner import AnalysisPlanner
from app.services.inventory_analyzer import InventoryAnalyzer


def plan_for(frame: pd.DataFrame) -> list[dict[str, object]]:
    available = AnalysisPlanner.available_fields_from_dataframe(frame)
    return AnalysisPlanner().plan(available, InventoryModule().capabilities())


def test_inventory_module_requires_a_reliable_field_pair() -> None:
    module = InventoryModule()

    assert module.match_score({"product_name"}) == 0.0
    assert module.match_score({"warehouse"}) == 0.0
    assert module.match_score({"product_id", "stock_quantity"}) > 0.5
    assert module.match_score({"stock_quantity", "safety_stock"}) > 0.5


def test_inventory_analyzer_calculates_supported_inventory_metrics_deterministically() -> None:
    frame = pd.DataFrame(
        {
            "product_id": ["P001", "P002", "P003"],
            "product_name": ["商品A", "商品B", "商品C"],
            "category": ["电子", "电子", "食品"],
            "stock_quantity": [5, 30, "无效"],
            "safety_stock": [10, 15, 8],
            "unit_cost": [20, 12, 9],
            "warehouse": ["郑州仓", "郑州仓", "北京仓"],
            "supplier": ["供应商甲", "供应商乙", "供应商甲"],
            "inbound_quantity": [10, 5, 2],
            "outbound_quantity": [8, 7, 1],
            "inventory_date": ["2026-01-02", "2026-01-01", "invalid"],
        }
    )

    analysis = InventoryAnalyzer().analyze(frame, plan_for(frame))

    assert analysis["inventory_count"] == 3
    assert analysis["stock_summary"] == {
        "count": 2,
        "total": 35.0,
        "average": 17.5,
        "maximum": 30.0,
        "minimum": 5.0,
        "median": 17.5,
    }
    assert analysis["low_stock_analysis"] == [
        {
            "product_id": "P001",
            "product_name": "商品A",
            "stock_quantity": 5.0,
            "safety_stock": 10.0,
            "shortage": 5.0,
        }
    ]
    assert analysis["inventory_value"] == {"count": 2, "total": 460.0, "average": 230.0}
    assert analysis["category_stock"] == [{"name": "电子", "value": 35.0}]
    assert analysis["warehouse_stock"] == [{"name": "郑州仓", "value": 35.0}]
    assert analysis["supplier_stock"] == [
        {"name": "供应商乙", "value": 30.0},
        {"name": "供应商甲", "value": 5.0},
    ]
    assert analysis["inventory_flow"] == {
        "total_inbound": 17.0,
        "total_outbound": 16.0,
        "net_change": 1.0,
    }
    assert analysis["inventory_trend"] == [
        {"name": "2026-01-01", "value": 30.0},
        {"name": "2026-01-02", "value": 5.0},
    ]


def test_inventory_analyzer_preserves_real_zero_and_skips_invalid_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "product_id": ["P001", "P002"],
            "stock_quantity": [0, "invalid"],
            "safety_stock": [1, 2],
            "unit_cost": [0, "invalid"],
        }
    )

    analysis = InventoryAnalyzer().analyze(frame, plan_for(frame))

    assert analysis["stock_summary"]["total"] == 0.0
    assert analysis["stock_summary"]["minimum"] == 0.0
    assert analysis["inventory_value"] == {"count": 1, "total": 0.0, "average": 0.0}
    assert analysis["low_stock_analysis"][0]["shortage"] == 1.0


def test_inventory_analyzer_returns_empty_or_none_for_unsupported_capabilities() -> None:
    frame = pd.DataFrame({"product_id": ["P001"]})

    analysis = InventoryAnalyzer().analyze(frame, plan_for(frame))

    assert analysis == {
        "inventory_count": 1,
        "stock_summary": None,
        "low_stock_analysis": [],
        "inventory_value": None,
        "category_stock": [],
        "warehouse_stock": [],
        "supplier_stock": [],
        "inventory_flow": None,
        "inventory_trend": [],
    }
