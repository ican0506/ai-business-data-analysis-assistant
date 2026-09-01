"""Turn verified Data Chat results into concise natural-language answers."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping

from app.core.config import get_settings
from app.services.ai_analysis_service import AIAnalysisService


logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Generate an answer without allowing the LLM to become a calculator."""

    _NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?")
    _METRIC_LABELS = {
        "sales_amount": "销售总额",
        "sales_quantity": "销售数量",
        "order_count": "订单数量",
        "average_order_value": "平均客单价",
    }

    def generate(
        self,
        question: str,
        query_plan: Mapping[str, object],
        result: Mapping[str, object],
        dataset_name: str,
        use_deepseek: bool | None = None,
    ) -> dict[str, str]:
        fallback = self._rule_based(question, query_plan, result)
        if use_deepseek is None:
            settings = get_settings()
            use_deepseek = AIAnalysisService.is_llm_enabled(settings)
        if not use_deepseek:
            return {"answer": fallback, "answer_mode": "rule_based"}

        prompt = self._build_prompt(question, query_plan, result, dataset_name)
        try:
            payload = AIAnalysisService._request_llm_json(prompt)
            answer = payload.get("answer") if isinstance(payload, dict) else None
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("LLM 返回空回答")
            if not self._numbers_are_grounded(answer, query_plan, result):
                raise ValueError("LLM 回答包含结构化结果之外的数字")
            return {"answer": answer.strip(), "answer_mode": get_settings().llm_provider}
        except Exception as error:
            logger.warning("Data Chat answer generation failed; using rule fallback error_type=%s", type(error).__name__)
            return {"answer": fallback, "answer_mode": "rule_based"}

    def _rule_based(
        self, question: str, query_plan: Mapping[str, object], result: Mapping[str, object]
    ) -> str:
        unavailable = result.get("unavailable") or []
        parts: list[str] = []
        metrics = result.get("metrics") or {}
        for metric in query_plan.get("metrics", []):
            metric_name = getattr(metric, "value", metric)
            value = metrics.get(metric_name)
            unavailable_item = next((item for item in unavailable if item.get("metric") == metric_name), None)
            label = self._METRIC_LABELS.get(metric_name, metric_name)
            if unavailable_item is not None or (isinstance(value, Mapping) and value.get("status") == "unavailable"):
                parts.append(f"当前数据缺少可用的{label}字段，因此无法计算{label}。")
                continue
            if value is None:
                continue
            if metric_name in {"sales_amount", "average_order_value"}:
                parts.append(f"{label}为{self._format_currency(value)}元。")
            elif metric_name in {"sales_quantity", "order_count"}:
                unit = "件" if metric_name == "sales_quantity" else "笔"
                parts.append(f"{label}为{self._format_number(value)}{unit}。")

        rows = result.get("rows") or result.get("groups") or []
        group_by = query_plan.get("group_by") or []
        group_name = getattr(group_by[0], "value", group_by[0]) if group_by else None
        if rows and group_name and group_name != "month":
            metric = getattr((query_plan.get("sort") or {}).get("metric") if isinstance(query_plan.get("sort"), Mapping) else None, "value", None)
            metric = metric or getattr(query_plan.get("metrics", ["sales_amount"])[0], "value", query_plan.get("metrics", ["sales_amount"])[0])
            label = self._METRIC_LABELS.get(metric, metric)
            formatted = []
            for row in rows:
                name = row.get(group_name)
                value = row.get(metric)
                if name is not None and value is not None:
                    suffix = "元" if metric in {"sales_amount", "average_order_value"} else ("件" if metric == "sales_quantity" else "笔")
                    formatted_value = self._format_currency(value) if suffix == "元" else self._format_number(value)
                    formatted.append(f"{name}（{formatted_value}{suffix}）")
            if formatted:
                parts.append(f"{label}排名前{len(formatted)}的{self._dimension_label(group_name)}为：" + "、".join(formatted) + "。")
        elif rows and group_name == "month":
            entries = []
            for row in rows:
                value = row.get("sales_amount")
                if value is not None:
                    entries.append(f"{row.get('month')}：{self._format_currency(value)}元")
            if entries:
                parts.append("月度销售额分别为：" + "、".join(entries) + "。")

        return "".join(parts) or "当前查询未返回可用的结构化指标结果。"

    @staticmethod
    def _dimension_label(group_name: str) -> str:
        return {"product": "商品", "category": "品类", "region": "区域"}.get(group_name, group_name)

    @staticmethod
    def _format_number(value: object) -> str:
        try:
            number = float(value)
            if number.is_integer():
                return f"{int(number):,}"
            return f"{number:,.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_currency(value: object) -> str:
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _build_prompt(question: str, query_plan: Mapping[str, object], result: Mapping[str, object], dataset_name: str) -> str:
        payload = {"question": question, "query_plan": query_plan, "result": result, "dataset_name": dataset_name}
        return (
            "你是数据分析结果解释助手。所有业务数字已经由 Python/Pandas 计算完成。\n"
            "只能把提供的结构化结果组织成简洁准确的中文回答，不得重新计算、修改数字、推测缺失数据或编造指标。\n"
            "不得声称看过原始 DataFrame，不得使用数据库、SQL、代码或工具。\n"
            "结果中 unavailable 的指标必须明确说明无法计算，不得解释为 0。只返回 JSON：{\"answer\":\"...\"}。\n"
            f"输入（仅包含已验证数据）：{json.dumps(payload, ensure_ascii=False, default=str)}"
        )

    def _numbers_are_grounded(self, answer: str, query_plan: Mapping[str, object], result: Mapping[str, object]) -> bool:
        allowed = set(self._NUMBER_RE.findall(json.dumps({"query_plan": query_plan, "result": result}, ensure_ascii=False, default=str)))
        normalized_allowed = {self._normalize_number(item) for item in allowed}
        for token in self._NUMBER_RE.findall(answer):
            if token not in allowed and self._normalize_number(token) not in normalized_allowed:
                return False
        return True

    @staticmethod
    def _normalize_number(value: str) -> str:
        try:
            return f"{float(value.replace(',', '')):.12g}"
        except ValueError:
            return value
