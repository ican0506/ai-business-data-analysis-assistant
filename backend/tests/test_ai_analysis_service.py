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


def student_analysis_plan(*supported_ids: str) -> list[dict]:
    capability_ids = (
        "student_count",
        "score_summary",
        "subject_score",
        "class_score",
        "student_score",
        "exam_trend",
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


def student_metrics(**analysis_overrides: object) -> dict:
    analysis = {
        "student_count": 3,
        "score_summary": {
            "count": 6,
            "average": 82.5,
            "maximum": 98.0,
            "minimum": 60.0,
            "median": 84.0,
        },
        "subject_score": [
            {"name": "数学", "count": 3, "average": 90.0, "maximum": 98.0, "minimum": 80.0},
            {"name": "英语", "count": 3, "average": 75.0, "maximum": 88.0, "minimum": 60.0},
        ],
        "class_score": [
            {"name": "一班", "count": 3, "average": 85.0, "maximum": 98.0, "minimum": 70.0},
            {"name": "二班", "count": 3, "average": 80.0, "maximum": 92.0, "minimum": 60.0},
        ],
        "student_score": [
            {"student_id": "S-1", "student_name": "张三", "score_count": 2, "average": 95.0, "maximum": 98.0, "minimum": 92.0},
        ],
        "exam_trend": [
            {"name": "期中", "average": 78.0, "count": 3},
            {"name": "期末", "average": 84.0, "count": 3},
        ],
    }
    analysis.update(analysis_overrides)
    supported_ids = tuple(
        capability_id
        for capability_id, value in analysis.items()
        if value is not None and value != []
    )
    return {
        "total_rows": 6,
        "selected_module": {"id": "student_score", "name": "学生成绩分析"},
        "available_fields": ["student_id", "score", "subject", "class_name", "exam_name"],
        "analysis_plan": student_analysis_plan(*supported_ids),
        "student_score_analysis": analysis,
        "sales_amount": None,
        "completion_rate": None,
        "growth_rate": None,
        "top_regions": [],
        "region_performance": [],
        "sales_volatility": None,
        "order_count": None,
        "product_quantity": [],
    }


def inventory_analysis_plan(*supported_ids: str) -> list[dict]:
    capability_ids = (
        "inventory_count",
        "stock_summary",
        "low_stock_analysis",
        "inventory_value",
        "category_stock",
        "warehouse_stock",
        "supplier_stock",
        "inventory_flow",
        "inventory_trend",
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


def inventory_metrics(**analysis_overrides: object) -> dict:
    inventory_analysis = {
        "inventory_count": 3,
        "stock_summary": {
            "count": 2,
            "total": 35.0,
            "average": 17.5,
            "maximum": 30.0,
            "minimum": 5.0,
            "median": 17.5,
        },
        "low_stock_analysis": [
            {"product_id": "P001", "product_name": "商品A", "stock_quantity": 5.0, "safety_stock": 10.0, "shortage": 5.0}
        ],
        "inventory_value": {"count": 2, "total": 460.0, "average": 230.0},
        "category_stock": [{"name": "电子", "value": 35.0}],
        "warehouse_stock": [{"name": "郑州仓", "value": 35.0}],
        "supplier_stock": [],
        "inventory_flow": None,
        "inventory_trend": [],
    }
    inventory_analysis.update(analysis_overrides)
    supported_ids = tuple(
        capability_id
        for capability_id, value in inventory_analysis.items()
        if value is not None and value != []
    )
    return {
        "total_rows": 3,
        "selected_module": {"id": "inventory", "name": "库存分析"},
        "available_fields": ["product_id", "stock_quantity", "safety_stock", "unit_cost", "warehouse"],
        "analysis_plan": inventory_analysis_plan(*supported_ids),
        "inventory_analysis": inventory_analysis,
        "sales_amount": None,
        "completion_rate": None,
        "growth_rate": None,
        "top_regions": [],
        "region_performance": [],
        "sales_volatility": None,
        "order_count": None,
        "product_quantity": [],
        "student_score_analysis": None,
    }


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


def test_student_score_fallback_interprets_only_calculated_score_metrics() -> None:
    insight = AIAnalysisService().analyze_metrics(student_metrics())

    assert insight["mode"] == "rule_based"
    assert "学生数量 3" in insight["summary"]
    assert "平均分 82.5" in insight["summary"]
    assert "数学" in insight["report"]
    assert "一班" in insight["report"]
    assert "张三" in insight["report"]
    assert "上升" in insight["report"]
    assert "销售额" not in insight["report"]
    assert "及格" not in insight["report"]
    assert insight["analysis_context"]["selected_module"]["id"] == "student_score"
    assert insight["analysis_context"]["supported_analyses"]["score_summary"]["average"] == 82.5


def test_student_score_fallback_distinguishes_unavailable_and_real_zero() -> None:
    unavailable = AIAnalysisService().analyze_metrics(
        student_metrics(score_summary=None, subject_score=[], class_score=[], exam_trend=[])
    )
    real_zero = AIAnalysisService().analyze_metrics(
        student_metrics(
            score_summary={
                "count": 2,
                "average": 0.0,
                "maximum": 0.0,
                "minimum": 0.0,
                "median": 0.0,
            },
            subject_score=[],
            class_score=[],
            exam_trend=[],
        )
    )

    assert "有效成绩数量" not in unavailable["summary"]
    assert "平均分 0.0" in real_zero["summary"]


def test_student_score_fallback_does_not_invent_missing_class_or_trend() -> None:
    insight = AIAnalysisService().analyze_metrics(
        student_metrics(class_score=[], exam_trend=[])
    )

    assert "班级" not in insight["report"]
    assert "趋势" not in insight["report"]


def test_student_score_deepseek_payload_excludes_order_metrics(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class SuccessfulCompletions:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][0]["content"]
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"summary": "成绩摘要"}'))]
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SuccessfulCompletions()))
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_kwargs: client))
    metrics = student_metrics()
    context = AIAnalysisService.build_analysis_context(metrics)
    result = AIAnalysisService._generate_with_deepseek(metrics, context, {"mode": "rule_based"})

    assert result["mode"] == "deepseek"
    assert "student_score_analysis" in captured["prompt"]
    assert "sales_amount" not in captured["prompt"]
    assert "不得假设 60 分为及格线" in captured["prompt"]


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


def test_deepseek_timeout_uses_configured_client_timeout_without_retries(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class TimeoutCompletions:
        def create(self, **_kwargs):
            raise TimeoutError("LLM timed out")

    def create_client(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(chat=SimpleNamespace(completions=TimeoutCompletions()))

    monkeypatch.setattr(
        "app.services.ai_analysis_service.get_settings",
        lambda: SimpleNamespace(
            llm_provider="deepseek",
            llm_api_key="test-key",
            llm_base_url="https://api.deepseek.com",
            llm_model="deepseek-chat",
            llm_timeout_seconds=25,
        ),
    )
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=create_client))
    fallback = {"mode": "rule_based", "summary": "安全回退"}

    result = AIAnalysisService._generate_with_deepseek(
        {"total_rows": 0},
        {"supported_analyses": {}, "skipped_analyses": []},
        fallback,
    )

    assert captured["timeout"] == 25
    assert captured["max_retries"] == 0
    assert result is fallback


def test_deepseek_request_enables_max_reasoning_without_temperature(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class SuccessfulCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"summary": "深度分析摘要"}'))]
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SuccessfulCompletions()))
    monkeypatch.setattr(
        "app.services.ai_analysis_service.get_settings",
        lambda: SimpleNamespace(
            llm_provider="deepseek",
            llm_api_key="test-key",
            llm_base_url="https://api.deepseek.com",
            llm_model="configured-deepseek-model",
            llm_timeout_seconds=25,
        ),
    )
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_kwargs: client))

    result = AIAnalysisService._generate_with_deepseek(
        {"total_rows": 0},
        {"supported_analyses": {}, "skipped_analyses": []},
        {"mode": "rule_based"},
    )

    assert result["mode"] == "deepseek"
    assert captured["model"] == "configured-deepseek-model"
    assert captured["reasoning_effort"] == "max"
    assert captured["extra_body"] == {"thinking": {"type": "enabled"}}
    assert captured["response_format"] == {"type": "json_object"}
    assert "temperature" not in captured


def test_inventory_fallback_uses_only_real_inventory_metrics() -> None:
    insight = AIAnalysisService().analyze_metrics(inventory_metrics())

    assert insight["mode"] == "rule_based"
    assert "库存总量 35.0" in insight["summary"]
    assert "库存价值总计 460.0" in insight["summary"]
    assert "低库存" in insight["report"]
    assert "销售额" not in insight["report"]
    assert "完成率" not in insight["report"]
    assert insight["analysis_context"]["selected_module"]["id"] == "inventory"
    assert insight["analysis_context"]["supported_analyses"]["inventory_count"] == 3


def test_inventory_deepseek_payload_and_prompt_exclude_order_metrics(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class SuccessfulCompletions:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][0]["content"]
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"summary": "库存摘要"}'))]
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SuccessfulCompletions()))
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_kwargs: client))
    metrics = inventory_metrics()
    context = AIAnalysisService.build_analysis_context(metrics)
    result = AIAnalysisService._generate_with_deepseek(metrics, context, {"mode": "rule_based"})

    assert result["mode"] == "deepseek"
    assert "inventory_analysis" in captured["prompt"]
    assert "sales_amount" not in captured["prompt"]
    assert "不得推断库存周转率" in captured["prompt"]


def test_order_analysis_context_and_deepseek_payload_keep_only_safe_aggregates() -> None:
    metrics = {
        "total_rows": 2,
        "selected_module": {"id": "order", "name": "订单分析"},
        "analysis_plan": [
            {"id": "order_count", "name": "订单数量分析", "supported": True},
            {"id": "sales_total", "name": "销售额分析", "supported": True},
            {"id": "customer_analysis", "name": "客户分析", "supported": True},
            {"id": "data_quality_analysis", "name": "数据质量分析", "supported": True},
        ],
        "order_analysis": {
            "overview": {"record_count": 2, "order_count": 2, "sales_total": 100.0, "average_order_value": 50.0},
            "customer_analysis": {"top_customers": [{"customer_id": "U-1", "customer_name": "张三", "order_count": 2, "sales_amount": 100.0}]},
            "data_quality": {
                "amount_mismatch_count": 1,
                "phone_invalid_count": 1,
                "email_invalid_count": 1,
                "phone": "13800000000",
                "email": "private@example.com",
            },
        },
    }

    context = AIAnalysisService.build_analysis_context(metrics)
    payload = AIAnalysisService._deepseek_metrics_payload(metrics, context)
    insight = AIAnalysisService().analyze_metrics(metrics)

    assert context["supported_analyses"]["sales_total"]["total"] == 100.0
    assert "customer_name" not in str(payload)
    assert "13800000000" not in str(payload)
    assert "private@example.com" not in str(payload)
    assert "可信销售额 100.0" in insight["summary"]
    assert "金额不一致" in insight["report"]
