from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from app.services.data_chat.answer_generator import AnswerGenerator


def _generator() -> AnswerGenerator:
    return AnswerGenerator()


def test_rule_based_answer_formats_single_and_multiple_metrics() -> None:
    answer = _generator().generate(
        question="销售额和销量是多少？",
        query_plan={"metrics": ["sales_amount", "sales_quantity"]},
        result={"metrics": {"sales_amount": 328560.5, "sales_quantity": 1842}},
        dataset_name="orders.csv",
        use_deepseek=False,
    )

    assert answer["answer_mode"] == "rule_based"
    assert "328,560.50" in answer["answer"]
    assert "1,842" in answer["answer"]


def test_rule_based_answer_supports_top_n_and_trend() -> None:
    top = _generator().generate(
        question="销售额排名前2的商品",
        query_plan={"metrics": ["sales_amount"], "group_by": ["product"], "limit": 2},
        result={"groups": [{"product": "A", "sales_amount": 56000}, {"product": "B", "sales_amount": 43000}]},
        dataset_name="orders.csv",
        use_deepseek=False,
    )
    trend = _generator().generate(
        question="月度趋势",
        query_plan={"metrics": ["sales_amount"], "group_by": ["month"]},
        result={"groups": [{"month": "2026-01", "sales_amount": 100000}, {"month": "2026-02", "sales_amount": 120000}]},
        dataset_name="orders.csv",
        use_deepseek=False,
    )

    assert "A（56,000.00元）" in top["answer"]
    assert "2026-01" in trend["answer"]


def test_rule_based_answer_distinguishes_unavailable_from_zero() -> None:
    unavailable = _generator().generate(
        question="销售数量是多少？",
        query_plan={"metrics": ["sales_quantity"]},
        result={"metrics": {"sales_quantity": {"status": "unavailable", "reason": "quantity 字段不可用于计算"}}},
        dataset_name="orders.csv",
        use_deepseek=False,
    )
    zero = _generator().generate(
        question="销售额是多少？",
        query_plan={"metrics": ["sales_amount"]},
        result={"metrics": {"sales_amount": 0}},
        dataset_name="orders.csv",
        use_deepseek=False,
    )

    assert "无法计算销售数量" in unavailable["answer"]
    assert "0.00" in zero["answer"]


def test_deepseek_failure_falls_back_without_losing_real_result() -> None:
    with patch("app.services.data_chat.answer_generator.AIAnalysisService._request_llm_json", side_effect=TimeoutError):
        answer = _generator().generate(
            question="销售额是多少？",
            query_plan={"metrics": ["sales_amount"]},
            result={"metrics": {"sales_amount": 100}},
            dataset_name="orders.csv",
            use_deepseek=True,
        )

    assert answer["answer_mode"] == "rule_based"
    assert "100.00" in answer["answer"]


def test_deepseek_prompt_contains_only_structured_inputs(monkeypatch) -> None:
    captured: list[str] = []
    monkeypatch.setattr(
        "app.services.data_chat.answer_generator.get_settings",
        lambda: SimpleNamespace(llm_provider="deepseek", llm_api_key="configured"),
    )

    def fake_request(prompt: str) -> dict:
        captured.append(prompt)
        return {"answer": "销售额为100.00元。"}

    with patch("app.services.data_chat.answer_generator.AIAnalysisService._request_llm_json", side_effect=fake_request):
        answer = _generator().generate(
            question="销售额是多少？",
            query_plan={"metrics": ["sales_amount"]},
            result={"metrics": {"sales_amount": 100}},
            dataset_name="orders.csv",
            use_deepseek=True,
        )

    assert answer["answer_mode"] == "deepseek"
    assert "order_id" not in captured[0]
    assert "数据库" in captured[0]
    assert "100" in captured[0]


def test_openrouter_uses_shared_llm_request_and_reports_provider_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.data_chat.answer_generator.get_settings",
        lambda: SimpleNamespace(llm_provider="openrouter", llm_api_key="configured"),
    )
    with patch(
        "app.services.data_chat.answer_generator.AIAnalysisService._request_llm_json",
        return_value={"answer": "销售额为100.00元。"},
    ) as request:
        answer = _generator().generate(
            question="销售额是多少？",
            query_plan={"metrics": ["sales_amount"]},
            result={"metrics": {"sales_amount": 100}},
            dataset_name="orders.csv",
        )

    assert request.call_count == 1
    assert answer["answer_mode"] == "openrouter"
