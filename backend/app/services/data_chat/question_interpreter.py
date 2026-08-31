"""Convert a narrow set of Chinese order questions into safe query plans."""

from __future__ import annotations

import calendar
import re
from datetime import date
from typing import Callable

import pandas as pd
from pydantic import ValidationError

from app.schemas.data_chat import (
    DataChatDateRange,
    DataChatFilters,
    DataChatGroupBy,
    DataChatMetric,
    DataChatQueryPlan,
    DataChatSort,
    DataChatSortDirection,
)
from app.services.ai_analysis_service import AIAnalysisService
from app.services.analysis_engine import AnalysisEngine
from app.services.order_analyzer import OrderAnalyzer


class QuestionClarificationRequired(ValueError):
    """The question has a known ambiguity that must not be guessed."""


class QueryPlanParseError(ValueError):
    """Neither a rule nor the constrained LLM payload produced a safe plan."""


class RuleBasedQuestionInterpreter:
    """Rule-first interpreter for the explicit Phase 2 Chinese question scope."""

    def __init__(self, analysis_engine: AnalysisEngine | None = None) -> None:
        self._analysis_engine = analysis_engine or AnalysisEngine()

    def interpret(
        self,
        question: str,
        dataframe: pd.DataFrame,
        field_overrides: dict[str, str] | None = None,
    ) -> DataChatQueryPlan | None:
        text = re.sub(r"\s+", "", question)
        metrics = self._metrics(text)
        if not metrics:
            return None

        mapped_frame, _context = self._analysis_engine.prepare_context(
            dataframe, field_overrides=field_overrides
        )
        date_range = self._date_range(text, mapped_frame)
        filters = self._filters(text, mapped_frame)
        if filters is None:
            return None
        group_by, sort, limit = self._grouping(text, metrics)
        return DataChatQueryPlan(
            metrics=metrics,
            date_range=date_range,
            filters=filters,
            group_by=group_by,
            sort=sort,
            limit=limit,
        )

    @staticmethod
    def _metrics(text: str) -> list[DataChatMetric]:
        metrics: list[DataChatMetric] = []
        if re.search(r"销售(?:总)?额|营业额|收入", text):
            metrics.append(DataChatMetric.SALES_AMOUNT)
        if re.search(r"销量|销售数量|销售总量|卖了多少(?:件|个|台)", text):
            metrics.append(DataChatMetric.SALES_QUANTITY)
        if re.search(r"订单(?:数量)?|多少单|几单", text):
            metrics.append(DataChatMetric.ORDER_COUNT)
        if re.search(r"客单价|平均每单|平均订单金额", text):
            metrics.append(DataChatMetric.AVERAGE_ORDER_VALUE)
        return list(dict.fromkeys(metrics))

    def _date_range(self, text: str, frame: pd.DataFrame) -> DataChatDateRange | None:
        full_dates = self._full_dates(text)
        if len(full_dates) >= 2 and re.search(r"到|至|~|—", text):
            return DataChatDateRange(start=full_dates[0], end=full_dates[1])

        month_range = re.search(
            r"(?P<year>20\d{2})年?(?P<start>1[0-2]|0?[1-9])月?(?:到|至|~|—)(?P<end>1[0-2]|0?[1-9])月",
            text,
        )
        if month_range:
            year = int(month_range.group("year"))
            start_month = int(month_range.group("start"))
            end_month = int(month_range.group("end"))
            if start_month > end_month:
                raise QuestionClarificationRequired("日期范围结束月份不能早于开始月份。")
            return self._month_range(year, start_month, end_month)

        day_range = re.search(
            r"(?P<start_month>1[0-2]|0?[1-9])月(?P<start_day>3[01]|[12]\d|0?[1-9])日?(?:到|至|~|—)(?P<end_month>1[0-2]|0?[1-9])月(?P<end_day>3[01]|[12]\d|0?[1-9])日?",
            text,
        )
        if day_range:
            year = self._infer_single_year(frame)
            try:
                return DataChatDateRange(
                    start=date(year, int(day_range.group("start_month")), int(day_range.group("start_day"))),
                    end=date(year, int(day_range.group("end_month")), int(day_range.group("end_day"))),
                )
            except ValueError as error:
                raise QuestionClarificationRequired("日期范围格式无效，请提供真实日期。") from error

        explicit_month = re.search(r"(?P<year>20\d{2})[年/-](?P<month>1[0-2]|0?[1-9])月?", text)
        if explicit_month:
            return self._month_range(int(explicit_month.group("year")), int(explicit_month.group("month")))

        implicit_month = re.search(r"(?<!\d)(?P<month>1[0-2]|0?[1-9])月(?:份)?", text)
        if implicit_month:
            return self._month_range(self._infer_single_year(frame), int(implicit_month.group("month")))
        return None

    @staticmethod
    def _full_dates(text: str) -> list[date]:
        matches = re.finditer(
            r"(?P<year>20\d{2})[年/-](?P<month>1[0-2]|0?[1-9])[月/-](?P<day>3[01]|[12]\d|0?[1-9])日?",
            text,
        )
        values: list[date] = []
        for match in matches:
            try:
                values.append(date(int(match.group("year")), int(match.group("month")), int(match.group("day"))))
            except ValueError as error:
                raise QuestionClarificationRequired("日期格式无效，请提供真实日期。") from error
        return values

    @staticmethod
    def _month_range(year: int, start_month: int, end_month: int | None = None) -> DataChatDateRange:
        actual_end_month = end_month or start_month
        return DataChatDateRange(
            start=date(year, start_month, 1),
            end=date(year, actual_end_month, calendar.monthrange(year, actual_end_month)[1]),
        )

    @staticmethod
    def _infer_single_year(frame: pd.DataFrame) -> int:
        values = OrderAnalyzer._parse_order_dates(frame["date"]) if "date" in frame else pd.Series(dtype="datetime64[ns]")
        years = sorted({int(value.year) for value in values.dropna()})
        if len(years) == 1:
            return years[0]
        if len(years) > 1:
            raise QuestionClarificationRequired("数据包含多个年份，请指定要查询哪一年的月份。")
        raise QuestionClarificationRequired("数据集中没有可识别日期，请指定完整日期范围或补充 date 字段。")

    @staticmethod
    def _filters(text: str, frame: pd.DataFrame) -> DataChatFilters | None:
        matched: dict[str, str] = {}
        for field in ("region", "product", "category"):
            if field not in frame:
                continue
            values = sorted(
                {
                    str(value).strip()
                    for value in frame[field].dropna().tolist()
                    if str(value).strip()
                },
                key=lambda value: (-len(value), value),
            )
            candidates = [value for value in values if value in text]
            if len(candidates) > 1:
                return None
            if candidates:
                matched[field] = candidates[0]

        region_hint = re.search(r"(?P<value>[\u4e00-\u9fffA-Za-z0-9_-]+)(?:地区|区域)", text)
        if region_hint and "region" not in matched:
            return None
        category_hint = re.search(r"(?P<value>[\u4e00-\u9fffA-Za-z0-9_-]+)(?:品类|分类)", text)
        if category_hint and "category" not in matched:
            return None
        return DataChatFilters(**matched)

    @staticmethod
    def _grouping(
        text: str, metrics: list[DataChatMetric]
    ) -> tuple[list[DataChatGroupBy], DataChatSort | None, int | None]:
        dimension_map = {"商品": DataChatGroupBy.PRODUCT, "品类": DataChatGroupBy.CATEGORY, "分类": DataChatGroupBy.CATEGORY, "地区": DataChatGroupBy.REGION, "区域": DataChatGroupBy.REGION}
        top = re.search(r"(?:最高|Top|TOP).*?(?P<limit>\d+)个?(?P<dimension>商品|品类|分类|地区|区域)|(?P<dimension_after>商品|品类|分类|地区|区域).*?(?:最高|Top|TOP).*?(?P<limit_after>\d+)", text)
        if top:
            dimension = top.group("dimension") or top.group("dimension_after")
            limit = int(top.group("limit") or top.group("limit_after"))
            sort_metric = DataChatMetric.SALES_QUANTITY if DataChatMetric.SALES_QUANTITY in metrics else DataChatMetric.SALES_AMOUNT
            return [dimension_map[dimension]], DataChatSort(metric=sort_metric, direction=DataChatSortDirection.DESC), limit
        if re.search(r"每月|每个月|月度.*趋势|销售趋势|趋势", text):
            return [DataChatGroupBy.MONTH], None, None
        return [], None, None


class LLMQuestionInterpreter:
    """Constrained fallback: an LLM can only emit a Pydantic-validated plan."""

    def __init__(self, request_json: Callable[[str], dict] | None = None) -> None:
        self._request_json = request_json or AIAnalysisService._request_deepseek_json

    def interpret(self, question: str) -> DataChatQueryPlan:
        prompt = (
            "你只负责将中文订单数据问题转换为 JSON QueryPlan，不是数据计算器。"
            "你不知道真实数据，不得计算、推断或输出任何业务数值。"
            "只能输出 JSON，不得输出 SQL、Python、Markdown、解释文字或额外字段。"
            "只允许 domain=order；metrics 只允许 sales_amount、sales_quantity、order_count、average_order_value；"
            "filters 只允许 region、product、category；group_by 只允许 product、category、region、month；"
            "sort 只允许 metrics 中的字段和 asc/desc；limit 为 1 到 100。"
            "无法安全解析时，输出 {\"domain\":\"unsupported\"}。\n"
            f"用户问题：{question}"
        )
        try:
            payload = self._request_json(prompt)
            return DataChatQueryPlan.model_validate(payload)
        except Exception as error:
            raise QueryPlanParseError("当前暂不支持该类型的数据查询。") from error
