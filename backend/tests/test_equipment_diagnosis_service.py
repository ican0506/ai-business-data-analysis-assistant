from app.services.ai_analysis_service import AIAnalysisService
from app.services.equipment_diagnosis_service import EquipmentDiagnosisService


def test_equipment_diagnosis_reuses_shared_deepseek_json_request(monkeypatch) -> None:
    requested_prompts: list[str] = []

    def fake_request(prompt: str) -> dict:
        requested_prompts.append(prompt)
        return {
            "risk_level": "高风险",
            "problem_analysis": "设备温度异常升高，可能存在机械磨损风险。",
            "possible_causes": ["轴承磨损"],
            "suggestions": ["检查润滑系统"],
        }

    monkeypatch.setattr(AIAnalysisService, "_request_deepseek_json", fake_request)
    fallback = {
        "equipment_name": "水泥磨",
        "risk_level": "中风险",
        "problem_analysis": "规则诊断",
        "possible_causes": ["规则原因"],
        "suggestions": ["规则建议"],
        "mode": "rule_based",
    }
    context = {"equipment": {"equipment_name": "水泥磨", "temperature": 84}, "alerts": []}

    diagnosis = EquipmentDiagnosisService._generate_with_deepseek(context, fallback)

    assert len(requested_prompts) == 1
    assert diagnosis["equipment_name"] == "水泥磨"
    assert diagnosis["risk_level"] == "高风险"
    assert diagnosis["possible_causes"] == ["轴承磨损"]
    assert diagnosis["mode"] == "deepseek"
