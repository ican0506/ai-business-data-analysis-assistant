from datetime import date

import pytest

from app.services.predictors.energy_consumption_predictor import EnergyConsumptionPredictor
from app.services.predictors.equipment_failure_predictor import EquipmentFailurePredictor
from app.services.predictors.production_completion_predictor import ProductionCompletionPredictor


def test_equipment_predictor_sorts_history_and_escalates_temperature_vibration_fault_and_status() -> None:
    records = [
        {
            "equipment_name": "水泥磨",
            "record_date": date(2026, 8, 3),
            "temperature": 84,
            "vibration": 5.2,
            "fault_count": 1,
            "status": "检修",
        },
        {
            "equipment_name": "水泥磨",
            "record_date": date(2026, 8, 1),
            "temperature": 72,
            "vibration": 3.4,
            "fault_count": 0,
            "status": "运行",
        },
        {
            "equipment_name": "水泥磨",
            "record_date": date(2026, 8, 2),
            "temperature": 78,
            "vibration": 4.3,
            "fault_count": 0,
            "status": "运行",
        },
    ]

    result = EquipmentFailurePredictor().predict(records)

    assert result["equipment_name"] == "水泥磨"
    assert result["predicted_temperature"] == pytest.approx(90.0)
    assert result["predicted_vibration"] == pytest.approx(6.1)
    assert result["risk_level"] == "高风险"
    assert any("温度" in reason for reason in result["reasons"])
    assert any("振动" in reason for reason in result["reasons"])
    assert any("故障" in reason for reason in result["reasons"])
    assert "24 小时" in result["maintenance_suggestion"]


def test_equipment_predictor_returns_insufficient_data_for_less_than_three_valid_readings() -> None:
    result = EquipmentFailurePredictor().predict(
        [
            {"equipment_name": "水泥磨", "record_date": "2026-08-01", "temperature": 70, "vibration": 3.0, "fault_count": 0, "status": "运行"},
            {"equipment_name": "水泥磨", "record_date": "2026-08-02", "temperature": None, "vibration": 3.5, "fault_count": 0, "status": "运行"},
            {"equipment_name": "水泥磨", "record_date": "2026-08-03", "temperature": 75, "vibration": 4.0, "fault_count": 0, "status": "运行"},
        ]
    )

    assert result["risk_level"] == "数据不足"
    assert result["predicted_temperature"] is None
    assert result["predicted_vibration"] is None


def test_energy_predictor_combines_moving_average_and_upward_trend_into_high_risk_warning() -> None:
    records = [
        {"production_line": "1号线", "record_date": "2026-08-03", "electricity_consumption": 80, "coal_consumption": 110, "unit_energy_consumption": 90},
        {"production_line": "1号线", "record_date": "2026-08-01", "electricity_consumption": 70, "coal_consumption": 100, "unit_energy_consumption": 60},
        {"production_line": "1号线", "record_date": "2026-08-02", "electricity_consumption": 75, "coal_consumption": 105, "unit_energy_consumption": 75},
    ]

    result = EnergyConsumptionPredictor().predict(records)

    assert result["production_line"] == "1号线"
    assert result["baseline_unit_energy_consumption"] == pytest.approx(75.0)
    assert result["predicted_unit_energy_consumption"] == pytest.approx(90.0)
    assert result["deviation_rate"] == pytest.approx(20.0)
    assert result["trend"] == "上升"
    assert result["warning_level"] == "高风险"


def test_energy_predictor_returns_insufficient_data_when_fewer_than_three_points() -> None:
    result = EnergyConsumptionPredictor().predict(
        [
            {"production_line": "1号线", "record_date": "2026-08-01", "unit_energy_consumption": 75},
            {"production_line": "1号线", "record_date": "2026-08-02", "unit_energy_consumption": 76},
        ]
    )

    assert result["warning_level"] == "数据不足"
    assert result["predicted_unit_energy_consumption"] is None


def test_energy_predictor_keeps_real_zero_energy_as_a_valid_value() -> None:
    result = EnergyConsumptionPredictor().predict(
        [
            {"production_line": "1号线", "record_date": "2026-08-01", "unit_energy_consumption": 0},
            {"production_line": "1号线", "record_date": "2026-08-02", "unit_energy_consumption": 0},
            {"production_line": "1号线", "record_date": "2026-08-03", "unit_energy_consumption": 0},
        ]
    )

    assert result["baseline_unit_energy_consumption"] == 0.0
    assert result["predicted_unit_energy_consumption"] == 0.0
    assert result["deviation_rate"] == 0.0
    assert result["warning_level"] == "正常"


def test_production_predictor_recalculates_completion_from_cement_output_not_stored_rate() -> None:
    records = [
        {"production_line": "1号线", "record_date": "2026-08-03", "cement_output": 120, "planned_output": 100, "completion_rate": 0},
        {"production_line": "1号线", "record_date": "2026-08-01", "cement_output": 80, "planned_output": 100, "completion_rate": 999},
        {"production_line": "1号线", "record_date": "2026-08-02", "cement_output": 100, "planned_output": 100, "completion_rate": 1},
    ]

    result = ProductionCompletionPredictor().predict(records)

    assert result["production_line"] == "1号线"
    assert result["completion_rate"] == pytest.approx(100.0)
    assert result["predicted_output"] == pytest.approx(120.0)
    assert result["trend"] == "上升"
    assert result["delay_risk"] is None


def test_production_predictor_only_evaluates_delay_when_target_date_is_given() -> None:
    records = [
        {"production_line": "1号线", "record_date": "2026-08-01", "cement_output": 50, "planned_output": 100},
        {"production_line": "1号线", "record_date": "2026-08-02", "cement_output": 50, "planned_output": 100},
        {"production_line": "1号线", "record_date": "2026-08-03", "cement_output": 50, "planned_output": 100},
    ]

    result = ProductionCompletionPredictor().predict(records, target_date=date(2026, 8, 3))

    assert result["completion_rate"] == pytest.approx(50.0)
    assert result["predicted_output"] == pytest.approx(50.0)
    assert result["trend"] == "平稳"
    assert result["delay_risk"] == "可能延期"
