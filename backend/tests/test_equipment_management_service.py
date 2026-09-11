from __future__ import annotations

from types import SimpleNamespace

from app.services.equipment_management_service import EquipmentManagementService


def _record(**overrides):
    values = {
        "equipment_name": "水泥磨",
        "date": __import__("datetime").date(2026, 8, 2),
        "status": "运行",
        "fault_count": 1,
        "temperature": 85.0,
        "vibration": 5.2,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_equipment_service_uses_moonbit_triggered_rules_but_preserves_alert_schema(monkeypatch) -> None:
    calls: list[dict] = []

    class FakeMoonBitService:
        def evaluate_equipment_risk(self, **kwargs):
            calls.append(kwargs)
            return {
                "risk_level": "高",
                "triggered_rules": ["fault_count", "temperature", "vibration"],
            }

    monkeypatch.setattr(
        "app.services.equipment_management_service.MoonBitService",
        lambda: FakeMoonBitService(),
    )

    alerts = EquipmentManagementService()._alerts_for_record(_record())

    assert calls == [{"temperature": 85.0, "vibration": 5.2, "fault_count": 1, "status": "运行"}]
    assert [item["rule_id"] for item in alerts] == ["fault_count", "temperature", "vibration"]
    assert alerts[0]["message"] == "故障次数为 1 次"
    assert "risk_level" not in alerts[0]


def test_equipment_service_keeps_existing_python_rules_when_moonbit_is_unavailable(monkeypatch) -> None:
    class UnavailableMoonBitService:
        def evaluate_equipment_risk(self, **kwargs):
            return None

    monkeypatch.setattr(
        "app.services.equipment_management_service.MoonBitService",
        lambda: UnavailableMoonBitService(),
    )

    alerts = EquipmentManagementService()._alerts_for_record(_record(status="停机"))

    assert [item["rule_id"] for item in alerts] == ["fault_count", "status", "temperature", "vibration"]
