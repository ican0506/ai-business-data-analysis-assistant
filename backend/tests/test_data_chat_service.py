from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from app.schemas.data_chat import DataChatMetric, DataChatQueryPlan
from app.services.data_chat.data_chat_service import DataChatService, DataChatServiceError
from app.services.data_chat.question_interpreter import QueryPlanParseError


class _RuleInterpreter:
    def interpret(self, _question: str, _frame: pd.DataFrame, **_kwargs: object) -> DataChatQueryPlan:
        return DataChatQueryPlan(metrics=[DataChatMetric.SALES_AMOUNT])


class _NoMatchRuleInterpreter:
    def interpret(self, _question: str, _frame: pd.DataFrame, **_kwargs: object) -> None:
        return None


class _LLMInterpreter:
    def __init__(self) -> None:
        self.called = False

    def interpret(self, _question: str) -> DataChatQueryPlan:
        self.called = True
        return DataChatQueryPlan(metrics=[DataChatMetric.SALES_AMOUNT])


class _MetricEngine:
    def __init__(self) -> None:
        self.received_overrides: dict[str, str] | None = None

    def query(self, _frame: pd.DataFrame, plan: DataChatQueryPlan, field_overrides: dict[str, str]) -> dict:
        self.received_overrides = field_overrides
        return {"status": "success", "metrics": {"sales_amount": 20.0}, "plan_metrics": [item.value for item in plan.metrics]}


class _AnswerGenerator:
    def generate(self, **_kwargs: object) -> dict[str, str]:
        return {"answer": "销售额为20.00元。", "answer_mode": "rule_based"}


def _service(dataset: object, engine: _MetricEngine | None = None) -> DataChatService:
    return DataChatService(
        metrics_service=SimpleNamespace(
            load_cleaned_frame=lambda _db, _dataset: pd.DataFrame(
                {"order_id": ["O-1"], "source_price": [10], "quantity": [2]}
            )
        ),
        field_mapping_service=SimpleNamespace(get_overrides=lambda _db, _dataset_id: {"source_price": "unit_price"}),
        rule_interpreter=_RuleInterpreter(),
        metric_query_engine=engine or _MetricEngine(),
        answer_generator=_AnswerGenerator(),
    )


def test_service_loads_the_latest_cleaned_frame_and_passes_mapping_overrides() -> None:
    dataset = SimpleNamespace(id=3, owner_id=7, original_filename="orders.csv")
    engine = _MetricEngine()

    result = _service(dataset, engine).query(
        SimpleNamespace(get=lambda _model, _id: dataset),
        SimpleNamespace(id=7),
        dataset_id=3,
        question="销售额是多少",
    )

    assert result["interpreter_mode"] == "rule"
    assert result["result"]["metrics"]["sales_amount"] == 20.0
    assert result["query_plan"]["metrics"] == ["sales_amount"]
    assert engine.received_overrides == {"source_price": "unit_price"}
    assert result["answer"] == "销售额为20.00元。"
    assert result["answer_mode"] == "rule_based"


def test_service_rejects_another_users_dataset_before_reading_data() -> None:
    dataset = SimpleNamespace(id=3, owner_id=8, original_filename="orders.csv")

    with pytest.raises(DataChatServiceError) as error:
        _service(dataset).query(
            SimpleNamespace(get=lambda _model, _id: dataset),
            SimpleNamespace(id=7),
            dataset_id=3,
            question="销售额是多少",
        )

    assert error.value.status_code == 403
    assert error.value.detail == "无权查询此数据集"


def test_service_turns_an_invalid_persisted_field_override_into_a_business_error() -> None:
    dataset = SimpleNamespace(id=3, owner_id=7, original_filename="orders.csv")
    service = DataChatService(
        metrics_service=SimpleNamespace(
            load_cleaned_frame=lambda _db, _dataset: pd.DataFrame(
                {"order_id": ["O-1"], "unit_price": [10], "quantity": [2]}
            )
        ),
        field_mapping_service=SimpleNamespace(get_overrides=lambda _db, _dataset_id: {"missing_source": "unit_price"}),
        rule_interpreter=_RuleInterpreter(),
        metric_query_engine=_MetricEngine(),
    )

    with pytest.raises(DataChatServiceError) as error:
        service.query(
            SimpleNamespace(get=lambda _model, _id: dataset),
            SimpleNamespace(id=7),
            dataset_id=3,
            question="sales amount",
        )

    assert error.value.status_code == 400


@pytest.mark.parametrize("provider", ["deepseek", "openrouter"])
def test_service_uses_llm_fallback_for_each_enabled_provider(monkeypatch, provider: str) -> None:
    llm_interpreter = _LLMInterpreter()
    service = DataChatService(
        rule_interpreter=_NoMatchRuleInterpreter(),
        llm_interpreter=llm_interpreter,
    )
    monkeypatch.setattr(
        "app.services.data_chat.data_chat_service.get_settings",
        lambda: SimpleNamespace(llm_provider=provider, llm_api_key="configured"),
    )

    plan, mode = service._resolve_plan("哪个地区销售额最高？", pd.DataFrame(), {})

    assert llm_interpreter.called is True
    assert mode == "llm"
    assert plan.metrics == [DataChatMetric.SALES_AMOUNT]


def test_service_does_not_call_llm_when_rule_based_provider_cannot_match(monkeypatch) -> None:
    llm_interpreter = _LLMInterpreter()
    service = DataChatService(
        rule_interpreter=_NoMatchRuleInterpreter(),
        llm_interpreter=llm_interpreter,
    )
    monkeypatch.setattr(
        "app.services.data_chat.data_chat_service.get_settings",
        lambda: SimpleNamespace(llm_provider="rule_based", llm_api_key="configured"),
    )

    with pytest.raises(QueryPlanParseError, match="当前暂不支持"):
        service._resolve_plan("哪个地区销售额最高？", pd.DataFrame(), {})

    assert llm_interpreter.called is False


def test_openrouter_query_plan_is_executed_by_metric_engine(monkeypatch) -> None:
    dataset = SimpleNamespace(id=3, owner_id=7, original_filename="orders.csv")
    llm_interpreter = _LLMInterpreter()
    engine = _MetricEngine()
    service = DataChatService(
        metrics_service=SimpleNamespace(
            load_cleaned_frame=lambda _db, _dataset: pd.DataFrame(
                {"order_id": ["O-1"], "source_price": [10], "quantity": [2]}
            )
        ),
        field_mapping_service=SimpleNamespace(
            get_overrides=lambda _db, _dataset_id: {"source_price": "unit_price"}
        ),
        rule_interpreter=_NoMatchRuleInterpreter(),
        llm_interpreter=llm_interpreter,
        metric_query_engine=engine,
        answer_generator=_AnswerGenerator(),
    )
    monkeypatch.setattr(
        "app.services.data_chat.data_chat_service.get_settings",
        lambda: SimpleNamespace(llm_provider="openrouter", llm_api_key="configured"),
    )

    result = service.query(
        SimpleNamespace(get=lambda _model, _id: dataset),
        SimpleNamespace(id=7),
        dataset_id=3,
        question="那个地区销售额最高？",
    )

    assert llm_interpreter.called is True
    assert result["interpreter_mode"] == "llm"
    assert engine.received_overrides == {"source_price": "unit_price"}
