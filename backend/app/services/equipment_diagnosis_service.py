import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.ai_analysis_service import AIAnalysisService
from app.services.equipment_management_service import EquipmentManagementService


logger = logging.getLogger(__name__)


class EquipmentDiagnosisService:
    """Produces explainable equipment diagnoses from the latest persisted record."""

    def __init__(self) -> None:
        self.equipment_service = EquipmentManagementService()

    def diagnose(self, db: Session, equipment_name: str) -> dict | None:
        equipment = self.equipment_service.get_latest(db, equipment_name)
        if equipment is None:
            return None

        alerts = [
            alert
            for alert in self.equipment_service.analyze_anomalies(db)
            if alert["equipment_name"] == equipment_name
        ]
        context = {"equipment": equipment, "alerts": alerts}
        fallback = self._build_rule_diagnosis(context)
        settings = get_settings()
        if settings.llm_provider == "deepseek" and settings.llm_api_key:
            return self._generate_with_deepseek(context, fallback)
        return fallback

    @staticmethod
    def _build_rule_diagnosis(context: dict) -> dict:
        equipment = context["equipment"]
        alert_ids = {alert["rule_id"] for alert in context["alerts"]}
        risk_level = "高风险" if any(alert["severity"] == "高" for alert in context["alerts"]) else "中风险" if context["alerts"] else "正常"

        if {"temperature", "vibration"}.issubset(alert_ids):
            problem_analysis = "设备温度异常升高，结合振动数据判断可能存在机械磨损风险。"
        elif "temperature" in alert_ids:
            problem_analysis = "设备温度异常升高，存在热负荷或润滑异常风险。"
        elif "vibration" in alert_ids:
            problem_analysis = "设备振动异常，可能存在机械松动或轴承磨损风险。"
        elif "fault_count" in alert_ids:
            problem_analysis = "最新运行记录存在故障，设备可靠性需要重点关注。"
        elif "status" in alert_ids:
            problem_analysis = f"设备当前状态为“{equipment['status']}”，需要核实停机或非运行原因。"
        else:
            problem_analysis = "最新运行记录未触发温度、振动、故障次数或运行状态异常规则。"

        causes: list[str] = []
        suggestions: list[str] = []
        if "temperature" in alert_ids:
            causes.extend(["润滑不足或润滑系统异常", "轴承磨损导致摩擦升温"])
            suggestions.extend(["检查润滑系统", "检查轴承状态"])
        if "vibration" in alert_ids:
            causes.extend(["轴承磨损或转子不平衡", "基础或连接件松动"])
            suggestions.append("复核机械紧固件和对中状态")
        if "fault_count" in alert_ids:
            causes.append("近期故障未完全排除")
            suggestions.append("核查故障记录并安排维护")
        if "status" in alert_ids:
            causes.append("设备处于停机或非运行状态")
            suggestions.append("确认停机原因和恢复计划")
        if not causes:
            causes.append("当前记录未显示明确异常原因")
            suggestions.append("保持例行点检并持续跟踪温度和振动趋势")

        return {
            "equipment_name": equipment["equipment_name"],
            "risk_level": risk_level,
            "problem_analysis": problem_analysis,
            "possible_causes": list(dict.fromkeys(causes)),
            "suggestions": list(dict.fromkeys(suggestions)),
            "mode": "rule_based",
        }

    @staticmethod
    def _generate_with_deepseek(context: dict, fallback: dict) -> dict:
        prompt = (
            "你是一名制造业设备运维分析师。只能依据以下最新设备记录和已触发的规则告警生成诊断。"
            "不得编造设备历史、寿命、故障概率、维修完成情况或未提供的传感器数据。"
            "风险等级只能为 高风险、中风险、正常；所有数值必须来自输入。"
            "返回 JSON：risk_level, problem_analysis, possible_causes, suggestions。\n"
            f"设备诊断上下文：{context}"
        )
        try:
            generated = AIAnalysisService._request_deepseek_json(prompt)
            risk_level = generated.get("risk_level")
            return {
                "equipment_name": fallback["equipment_name"],
                "risk_level": risk_level if risk_level in {"高风险", "中风险", "正常"} else fallback["risk_level"],
                "problem_analysis": generated.get("problem_analysis") if isinstance(generated.get("problem_analysis"), str) else fallback["problem_analysis"],
                "possible_causes": EquipmentDiagnosisService._string_list(generated.get("possible_causes"), fallback["possible_causes"]),
                "suggestions": EquipmentDiagnosisService._string_list(generated.get("suggestions"), fallback["suggestions"]),
                "mode": "deepseek",
            }
        except Exception as error:
            logger.warning("Equipment diagnosis LLM failed; using rule fallback error_type=%s", type(error).__name__)
            return fallback

    @staticmethod
    def _string_list(value: object, fallback: list[str]) -> list[str]:
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return value
        return fallback
