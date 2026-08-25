from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.manufacturing import EnergyRecord, EquipmentRecord, ProductionRecord
from app.models.user import Base, User
from app.services.manufacturing_prediction_service import ManufacturingPredictionService


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
        username="prediction_service_owner",
        email="prediction-service@example.com",
        password_hash="not-used",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def _seed_operational_history(db: Session) -> None:
    db.add_all(
        [
            EquipmentRecord(date=date(2026, 8, 1), equipment_name="水泥磨", status="运行", running_hours=22, fault_count=0, temperature=70, vibration=3.1),
            EquipmentRecord(date=date(2026, 8, 2), equipment_name="水泥磨", status="运行", running_hours=22, fault_count=0, temperature=75, vibration=3.8),
            EquipmentRecord(date=date(2026, 8, 3), equipment_name="水泥磨", status="检修", running_hours=12, fault_count=1, temperature=82, vibration=5.2),
            EnergyRecord(date=date(2026, 8, 1), production_line="1号线", electricity_consumption=70, coal_consumption=100, unit_energy_consumption=70),
            EnergyRecord(date=date(2026, 8, 2), production_line="1号线", electricity_consumption=75, coal_consumption=105, unit_energy_consumption=75),
            EnergyRecord(date=date(2026, 8, 3), production_line="1号线", electricity_consumption=80, coal_consumption=110, unit_energy_consumption=90),
            ProductionRecord(date=date(2026, 8, 1), production_line="1号线", clinker_output=80, cement_output=80, planned_output=100, completion_rate=0, running_hours=22, downtime_hours=2),
            ProductionRecord(date=date(2026, 8, 2), production_line="1号线", clinker_output=100, cement_output=100, planned_output=100, completion_rate=0, running_hours=22, downtime_hours=2),
            ProductionRecord(date=date(2026, 8, 3), production_line="1号线", clinker_output=120, cement_output=120, planned_output=100, completion_rate=0, running_hours=22, downtime_hours=2),
        ]
    )
    db.commit()


def test_service_generates_equipment_prediction_and_persists_snapshot(db: Session, user: User) -> None:
    _seed_operational_history(db)

    created = ManufacturingPredictionService().generate_prediction(
        db, user.id, prediction_type="equipment_risk", scope_name="水泥磨"
    )

    equipment = created["prediction_result"]["equipment_predictions"][0]
    assert created["prediction_type"] == "equipment_risk"
    assert equipment["equipment_name"] == "水泥磨"
    assert equipment["risk_level"] == "高风险"
    assert created["data_snapshot"]["equipment_data_summary"]["record_count"] == 3


def test_service_generates_energy_prediction_and_persists_result(db: Session, user: User) -> None:
    _seed_operational_history(db)

    created = ManufacturingPredictionService().generate_prediction(
        db, user.id, prediction_type="energy_consumption", scope_name="1号线"
    )

    energy = created["prediction_result"]["energy_prediction"]
    assert created["prediction_type"] == "energy_consumption"
    assert energy["production_line"] == "1号线"
    assert energy["warning_level"] == "高风险"
    assert created["data_snapshot"]["energy_data_summary"]["record_count"] == 3


def test_service_generates_production_prediction_and_persists_result(db: Session, user: User) -> None:
    _seed_operational_history(db)

    created = ManufacturingPredictionService().generate_prediction(
        db,
        user.id,
        prediction_type="production_completion",
        scope_name="1号线",
        target_date=date(2026, 8, 3),
    )

    production = created["prediction_result"]["production_prediction"]
    assert created["prediction_type"] == "production_completion"
    assert production["completion_rate"] == pytest.approx(100.0)
    assert production["delay_risk"] == "无延期风险"
    assert created["data_snapshot"]["production_data_summary"]["record_count"] == 3


def test_service_returns_data_insufficient_results_without_operational_history(db: Session, user: User) -> None:
    created = ManufacturingPredictionService().generate_prediction(
        db, user.id, prediction_type="equipment_risk"
    )

    result = created["prediction_result"]
    assert created["risk_level"] == "数据不足"
    assert result["equipment_predictions"][0]["risk_level"] == "数据不足"
    assert result["energy_prediction"]["warning_level"] == "数据不足"
    assert result["production_prediction"]["trend"] == "数据不足"


def test_service_returns_immutable_persisted_snapshot_after_caller_mutates_result(db: Session, user: User) -> None:
    _seed_operational_history(db)
    service = ManufacturingPredictionService()
    created = service.generate_prediction(db, user.id, prediction_type="equipment_risk")

    created["data_snapshot"]["equipment_data_summary"]["record_count"] = 0
    created["prediction_result"]["equipment_predictions"][0]["risk_level"] = "正常"
    detail = service.get_prediction_detail(db, user.id, created["id"])

    assert detail is not None
    assert detail["data_snapshot"]["equipment_data_summary"]["record_count"] == 3
    assert detail["prediction_result"]["equipment_predictions"][0]["risk_level"] == "高风险"
