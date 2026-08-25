from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.manufacturing import EquipmentRecord
from app.models.user import Base, User
from app.services.ai_analysis_service import AIAnalysisService
from app.services.manufacturing_prediction_service import ManufacturingPredictionService
from app.services.prediction_explanation_service import PredictionExplanationService


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def user(db: Session) -> User:
    account = User(
        username="prediction_explanation_owner",
        email="prediction-explanation@example.com",
        password_hash="not-used",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def _prediction_result() -> dict:
    return {
        "equipment_predictions": [
            {
                "equipment_name": "水泥磨",
                "predicted_temperature": 88.0,
                "predicted_vibration": 5.4,
                "risk_level": "高风险",
                "reasons": ["温度持续升高", "振动持续升高"],
                "maintenance_suggestion": "安排设备巡检",
            }
        ],
        "energy_prediction": {"warning_level": "正常", "trend": "平稳"},
        "production_prediction": {"trend": "平稳", "delay_risk": "无延期风险"},
    }


def test_service_uses_ai_explanation_with_only_deterministic_prediction_context(monkeypatch) -> None:
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        "app.services.prediction_explanation_service.get_settings",
        lambda: SimpleNamespace(llm_provider="deepseek", llm_api_key="test-key"),
    )

    def fake_request(prompt: str) -> dict:
        captured["prompt"] = prompt
        return {
            "summary": "设备存在需要关注的确定性风险趋势。",
            "risk_explanation": "高风险等级来自温度与振动持续升高。",
            "suggestions": ["安排设备巡检"],
        }

    monkeypatch.setattr(AIAnalysisService, "_request_deepseek_json", staticmethod(fake_request))

    result = PredictionExplanationService().explain(
        prediction_result=_prediction_result(),
        data_snapshot={"raw_private_note": "不得发送给模型"},
        risk_level="高风险",
    )

    assert result == {
        "summary": "设备存在需要关注的确定性风险趋势。",
        "risk_explanation": "高风险等级来自温度与振动持续升高。",
        "suggestions": ["安排设备巡检"],
        "mode": "deepseek",
    }
    assert "prediction_result" in captured["prompt"]
    assert "risk_level" in captured["prompt"]
    assert "deterministic_reasons" in captured["prompt"]
    assert "raw_private_note" not in captured["prompt"]
    assert "不得发送给模型" not in captured["prompt"]


def test_service_falls_back_to_rule_based_explanation_when_ai_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.prediction_explanation_service.get_settings",
        lambda: SimpleNamespace(llm_provider="deepseek", llm_api_key=""),
    )

    result = PredictionExplanationService().explain(
        prediction_result=_prediction_result(),
        data_snapshot={},
        risk_level="高风险",
    )

    assert result["mode"] == "rule_based"
    assert "温度持续升高" in result["summary"]
    assert result["suggestions"] == ["安排设备巡检"]


def test_ai_explanation_cannot_change_deterministic_risk_level_or_snapshot(db: Session, user: User, monkeypatch) -> None:
    db.add_all(
        [
            EquipmentRecord(date=date(2026, 8, 1), equipment_name="水泥磨", status="运行", running_hours=22, fault_count=0, temperature=70, vibration=3.1),
            EquipmentRecord(date=date(2026, 8, 2), equipment_name="水泥磨", status="运行", running_hours=22, fault_count=0, temperature=76, vibration=4.0),
            EquipmentRecord(date=date(2026, 8, 3), equipment_name="水泥磨", status="检修", running_hours=12, fault_count=1, temperature=84, vibration=5.2),
        ]
    )
    db.commit()
    monkeypatch.setattr(
        "app.services.prediction_explanation_service.get_settings",
        lambda: SimpleNamespace(llm_provider="deepseek", llm_api_key="test-key"),
    )
    monkeypatch.setattr(
        AIAnalysisService,
        "_request_deepseek_json",
        staticmethod(
            lambda prompt: {
                "summary": "仅解释确定性结果。",
                "risk_explanation": "模型不能覆盖风险等级。",
                "suggestions": ["安排设备巡检"],
                "risk_level": "正常",
            }
        ),
    )

    created = ManufacturingPredictionService().generate_prediction(
        db,
        user.id,
        prediction_type="equipment_risk",
        scope_name="水泥磨",
    )

    assert created["risk_level"] == "高风险"
    assert created["ai_mode"] == "deepseek"
    explanation = created["data_snapshot"]["prediction_explanation"]
    assert explanation["summary"] == "仅解释确定性结果。"
    assert explanation["mode"] == "deepseek"
    assert "risk_level" not in explanation
