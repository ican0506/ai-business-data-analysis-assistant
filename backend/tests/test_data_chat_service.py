from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from app.schemas.data_chat import DataChatMetric, DataChatQueryPlan
from app.services.data_chat.data_chat_service import DataChatService, DataChatServiceError


class _RuleInterpreter:
    def interpret(self, _question: str, _frame: pd.DataFrame, **_kwargs: object) -> DataChatQueryPlan:
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
