import logging
from typing import Any

from app.core.config import get_settings
from app.services.ai_analysis_service import AIAnalysisService


logger = logging.getLogger(__name__)


class PredictionExplanationService:
    """Explain deterministic manufacturing forecasts without changing them."""

    def explain(
        self,
        *,
        prediction_result: dict,
        data_snapshot: dict,
        risk_level: str,
    ) -> dict:
        """Return an AI explanation or a deterministic fallback for one prediction run.

        ``data_snapshot`` deliberately remains outside the LLM prompt.  It is accepted
        at this orchestration boundary so callers can keep one complete immutable
        snapshot, while the provider receives only the approved prediction context.
        """
        deterministic_reasons = self._deterministic_reasons(prediction_result)
        fallback = self._build_rule_explanation(
            prediction_result=prediction_result,
            risk_level=risk_level,
            deterministic_reasons=deterministic_reasons,
        )
        settings = get_settings()
        if settings.llm_provider != "deepseek" or not settings.llm_api_key:
            return fallback

        prompt = self._build_prompt(
            prediction_result=prediction_result,
            risk_level=risk_level,
            deterministic_reasons=deterministic_reasons,
        )
        try:
            generated = AIAnalysisService._request_deepseek_json(prompt)
        except Exception as error:
            logger.warning(
                "Prediction explanation failed; using rule-based fallback provider=%s error_type=%s",
                settings.llm_provider,
                type(error).__name__,
            )
            return fallback
        return self._validated_ai_explanation(generated, fallback)

    @staticmethod
    def _build_prompt(
        *,
        prediction_result: dict,
        risk_level: str,
        deterministic_reasons: list[str],
    ) -> str:
        approved_context = {
            "prediction_result": prediction_result,
            "risk_level": risk_level,
            "deterministic_reasons": deterministic_reasons,
        }
        return (
            "你是制造业预测解释助手。只能解释以下 Python 确定性预测上下文。"
            "风险等级由 Python 预先确定，绝对不得修改、重算或输出新的风险等级。"
            "不得创建新的数值、预测概率、故障记录、传感器数据、设备信息或业务事实。"
            "不得依据未提供的信息推断原因。建议必须直接对应已提供的确定性原因或预测结果。"
            "仅返回 JSON 对象，字段必须是 summary、risk_explanation、suggestions；"
            "suggestions 必须为字符串数组。\n"
            f"确定性上下文：{approved_context}"
        )

    @staticmethod
    def _validated_ai_explanation(generated: Any, fallback: dict) -> dict:
        if not isinstance(generated, dict):
            return fallback
        summary = generated.get("summary")
        risk_explanation = generated.get("risk_explanation")
        suggestions = generated.get("suggestions")
        if not isinstance(summary, str) or not summary.strip():
            return fallback
        if not isinstance(risk_explanation, str) or not risk_explanation.strip():
            return fallback
        if not isinstance(suggestions, list) or not all(
            isinstance(item, str) and item.strip() for item in suggestions
        ):
            return fallback
        return {
            "summary": summary.strip(),
            "risk_explanation": risk_explanation.strip(),
            "suggestions": [item.strip() for item in suggestions],
            "mode": "deepseek",
        }

    @staticmethod
    def _deterministic_reasons(prediction_result: dict) -> list[str]:
        reasons: list[str] = []
        for prediction in prediction_result.get("equipment_predictions") or []:
            equipment_name = prediction.get("equipment_name") or "设备"
            for reason in prediction.get("reasons") or []:
                if isinstance(reason, str) and reason.strip():
                    reasons.append(f"{equipment_name}：{reason.strip()}")

        energy_prediction = prediction_result.get("energy_prediction") or {}
        energy_warning = energy_prediction.get("warning_level")
        energy_trend = energy_prediction.get("trend")
        if energy_warning and energy_warning != "数据不足":
            reasons.append(f"单位能耗预警等级为 {energy_warning}")
        if energy_trend and energy_trend != "数据不足":
            reasons.append(f"单位能耗预测趋势为 {energy_trend}")

        production_prediction = prediction_result.get("production_prediction") or {}
        production_trend = production_prediction.get("trend")
        delay_risk = production_prediction.get("delay_risk")
        if production_trend and production_trend != "数据不足":
            reasons.append(f"生产完成预测趋势为 {production_trend}")
        if delay_risk and delay_risk != "数据不足":
            reasons.append(f"生产延期判断为 {delay_risk}")
        return list(dict.fromkeys(reasons))

    @staticmethod
    def _build_rule_explanation(
        *,
        prediction_result: dict,
        risk_level: str,
        deterministic_reasons: list[str],
    ) -> dict:
        if risk_level == "数据不足":
            summary = "当前有效历史记录不足，无法形成可靠的确定性趋势预测。"
            risk_explanation = "风险等级为数据不足，原因是预测器缺少满足最低历史长度要求的数据。"
        elif deterministic_reasons:
            summary = "；".join(deterministic_reasons) + "。"
            risk_explanation = f"当前风险等级为 {risk_level}，仅基于上述 Python 确定性预测证据。"
        else:
            summary = "当前预测未产生可用于解释的额外确定性原因。"
            risk_explanation = f"当前风险等级为 {risk_level}，由 Python 预测器确定。"

        suggestions: list[str] = []
        for prediction in prediction_result.get("equipment_predictions") or []:
            suggestion = prediction.get("maintenance_suggestion")
            if isinstance(suggestion, str) and suggestion.strip():
                suggestions.append(suggestion.strip())
        energy_prediction = prediction_result.get("energy_prediction") or {}
        if energy_prediction.get("warning_level") in {"中风险", "高风险"}:
            suggestions.append("持续核查单位能耗趋势，并结合生产线运行记录复盘能耗变化。")
        production_prediction = prediction_result.get("production_prediction") or {}
        if production_prediction.get("delay_risk") == "可能延期":
            suggestions.append("复盘计划产量与实际产量的偏差，及时调整生产排程。")
        if not suggestions and risk_level != "数据不足":
            suggestions.append("持续补充后续运行记录，以验证当前确定性预测趋势。")

        return {
            "summary": summary,
            "risk_explanation": risk_explanation,
            "suggestions": list(dict.fromkeys(suggestions)),
            "mode": "rule_based",
        }
