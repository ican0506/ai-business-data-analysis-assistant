from __future__ import annotations

import pandas as pd
import pytest

from app.schemas.data_chat import DataChatMetric
from app.services.data_chat.question_interpreter import (
    LLMQuestionInterpreter,
    QuestionClarificationRequired,
    QueryPlanParseError,
    RuleBasedQuestionInterpreter,
)


def _frame(dates: list[str] | None = None) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2"],
            "product": ["手机", "耳机"],
            "category": ["数码", "配件"],
            "region": ["华东", "华南"],
            "unit_price": [100, 50],
            "quantity": [2, 3],
            "date": dates or ["2026-05-01", "2026-06-01"],
        }
    )


def test_rule_interpreter_parses_month_metrics_filters_top_n_and_trend() -> None:
    interpreter = RuleBasedQuestionInterpreter()

    may = interpreter.interpret("2026年5月销售总额和销售数量是多少？", _frame())
    top = interpreter.interpret("销售额最高的5个商品", _frame())
    region = interpreter.interpret("华东地区销售额是多少", _frame())
    trend = interpreter.interpret("每个月销售额趋势", _frame())

    assert may is not None
    assert may.metrics == [DataChatMetric.SALES_AMOUNT, DataChatMetric.SALES_QUANTITY]
    assert may.date_range.start.isoformat() == "2026-05-01"
    assert may.date_range.end.isoformat() == "2026-05-31"
    assert top is not None and top.group_by[0].value == "product" and top.limit == 5
    assert region is not None and region.filters.region == "华东"
    assert trend is not None and trend.group_by[0].value == "month"


@pytest.mark.parametrize(
    ("question", "metric", "dimension"),
    [
        ("哪个地区销售额最高？", DataChatMetric.SALES_AMOUNT, "region"),
        ("销售额最高的商品是什么？", DataChatMetric.SALES_AMOUNT, "product"),
        ("哪个品类销售额最高？", DataChatMetric.SALES_AMOUNT, "category"),
        ("哪个商品销量最高？", DataChatMetric.SALES_QUANTITY, "product"),
    ],
)
def test_rule_interpreter_parses_top_one_questions(question: str, metric: DataChatMetric, dimension: str) -> None:
    plan = RuleBasedQuestionInterpreter().interpret(question, _frame())

    assert plan is not None
    assert plan.metrics == [metric]
    assert [item.value for item in plan.group_by] == [dimension]
    assert plan.sort is not None and plan.sort.direction.value == "desc"
    assert plan.limit == 1


def test_rule_interpreter_keeps_an_explicit_top_n_limit() -> None:
    plan = RuleBasedQuestionInterpreter().interpret("销售额最高的5个商品是什么？", _frame())

    assert plan is not None
    assert plan.limit == 5


def test_rule_interpreter_requires_year_for_an_ambiguous_month() -> None:
    frame = _frame(["2025-05-01", "2026-05-01"])

    with pytest.raises(QuestionClarificationRequired, match="多个年份"):
        RuleBasedQuestionInterpreter().interpret("5月份销售额是多少", frame)


def test_rule_interpreter_uses_the_single_dataset_year_for_month_without_year() -> None:
    plan = RuleBasedQuestionInterpreter().interpret("5月份有多少订单", _frame())

    assert plan is not None
    assert plan.metrics == [DataChatMetric.ORDER_COUNT]
    assert plan.date_range.start.isoformat() == "2026-05-01"


def test_llm_interpreter_rejects_any_payload_that_is_not_a_query_plan() -> None:
    interpreter = LLMQuestionInterpreter(request_json=lambda _prompt: {"raw_sql": "SELECT * FROM datasets"})

    with pytest.raises(QueryPlanParseError):
        interpreter.interpret("帮我写一段 SQL")


def test_llm_interpreter_turns_provider_failures_into_safe_parse_errors() -> None:
    def raise_timeout(_prompt: str) -> dict:
        raise TimeoutError("provider timed out")

    interpreter = LLMQuestionInterpreter(request_json=raise_timeout)

    with pytest.raises(QueryPlanParseError):
        interpreter.interpret("帮我分析一下未来走势")
