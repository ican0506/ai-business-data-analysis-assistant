import sys
from types import SimpleNamespace

from app.services.ai_analysis_service import AIAnalysisService


def analysis_plan(*supported_ids: str) -> list[dict]:
    capability_ids = (
        "order_count",
        "product_quantity",
        "sales_total",
        "region_sales",
        "sales_trend",
        "target_completion",
    )
    return [
        {
            "id": capability_id,
            "name": capability_id,
            "supported": capability_id in supported_ids,
            "missing_fields": [] if capability_id in supported_ids else ["missing_field"],
            "reason": None if capability_id in supported_ids else "缺少所需字段",
        }
        for capability_id in capability_ids
    ]


def test_analyze_metrics_returns_business_insight_json() -> None:
    metrics = {
        "total_rows": 2,
        "sales_amount": {"total": 1200, "average": 600},
        "completion_rate": 60.0,
        "growth_rate": -50.0,
        "highest_sales_region": {"name": "east", "value": 800},
        "lowest_sales_region": {"name": "south", "value": 400},
        "region_performance": [
            {"name": "east", "sales_amount": 800, "target_amount": 1000, "completion_rate": 80.0},
            {"name": "south", "sales_amount": 400, "target_amount": 1000, "completion_rate": 40.0},
        ],
        "sales_volatility": {"standard_deviation": 200, "coefficient_of_variation": 33.33},
    }

    insight = AIAnalysisService().analyze_metrics(metrics)

    assert {"summary", "anomalies", "business_problems", "recommendations"} <= insight.keys()
    assert isinstance(insight["summary"], str)
    assert isinstance(insight["anomalies"], list)
    assert isinstance(insight["business_problems"], list)
    assert isinstance(insight["recommendations"], list)
    assert "metrics" not in insight


def test_analyze_metrics_skips_unavailable_sales_without_treating_it_as_zero() -> None:
    metrics = {
        "total_rows": 2,
        "sales_amount": None,
        "completion_rate": None,
        "growth_rate": None,
        "top_regions": [],
        "region_performance": [],
        "sales_volatility": None,
        "order_count": 2,
        "product_quantity": [{"name": "A", "value": 5}],
        "analysis_plan": analysis_plan("order_count", "product_quantity"),
        "available_fields": ["order_id", "product", "quantity"],
    }

    insight = AIAnalysisService().analyze_metrics(metrics)

    assert "订单数量" in insight["summary"]
    assert "商品销量" in insight["summary"]
    assert "销售额" not in insight["summary"]
    assert insight["analysis_context"]["supported_analyses"]["order_count"] == 2
    assert any(item["id"] == "sales_total" for item in insight["analysis_context"]["skipped_analyses"])


def test_analyze_metrics_preserves_a_real_zero_sales_amount() -> None:
    metrics = {
        "total_rows": 1,
        "sales_amount": {"total": 0, "average": 0, "maximum": 0, "minimum": 0},
        "completion_rate": None,
        "growth_rate": None,
        "top_regions": [],
        "region_performance": [],
        "sales_volatility": {"standard_deviation": None, "coefficient_of_variation": None},
        "order_count": None,
        "product_quantity": [],
        "analysis_plan": analysis_plan("sales_total"),
        "available_fields": ["sales_amount"],
    }

    insight = AIAnalysisService().analyze_metrics(metrics)

    assert "销售额总计 0" in insight["summary"]
    assert "sales_total" in insight["analysis_context"]["supported_analyses"]


def test_analysis_context_only_keeps_calculated_supported_metrics() -> None:
    metrics = {
        "total_rows": 1,
        "sales_amount": {"total": 100, "average": 100},
        "completion_rate": None,
        "growth_rate": None,
        "top_regions": [],
        "region_performance": [],
        "sales_volatility": None,
        "order_count": None,
        "product_quantity": [],
        "analysis_plan": analysis_plan("sales_total", "region_sales", "sales_trend"),
        "available_fields": ["sales_amount", "region", "date"],
    }

    context = AIAnalysisService().build_analysis_context(metrics)

    assert context["supported_analyses"] == {"sales_total": {"total": 100, "average": 100}}
    skipped_ids = {item["id"] for item in context["skipped_analyses"]}
    assert {"region_sales", "sales_trend"} <= skipped_ids


def test_analyze_metrics_without_region_or_target_does_not_invent_them() -> None:
    metrics = {
        "total_rows": 1,
        "sales_amount": {"total": 100, "average": 100},
        "completion_rate": None,
        "growth_rate": None,
        "top_regions": [],
        "region_performance": [],
        "sales_volatility": None,
        "order_count": None,
        "product_quantity": [],
        "analysis_plan": analysis_plan("sales_total"),
        "available_fields": ["sales_amount"],
    }

    insight = AIAnalysisService().analyze_metrics(metrics)

    assert "销售额总计 100" in insight["summary"]
    assert "区域" not in insight["report"]
    assert "完成率" not in insight["report"]


def test_deepseek_failure_returns_rule_based_fallback(monkeypatch) -> None:
    class FailingCompletions:
        def create(self, **_kwargs):
            raise RuntimeError("DeepSeek unavailable")

    client = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_kwargs: client))
    fallback = {"mode": "rule_based", "summary": "安全回退"}

    result = AIAnalysisService._generate_with_deepseek(
        {"total_rows": 0},
        {"supported_analyses": {}, "skipped_analyses": []},
        fallback,
    )

    assert result is fallback
