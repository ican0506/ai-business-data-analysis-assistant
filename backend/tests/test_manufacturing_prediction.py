from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.models.user import Base, User
from app.schemas.manufacturing_prediction import ManufacturingPredictionSnapshotCreate
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
        username="prediction_owner",
        email="prediction@example.com",
        password_hash="not-used",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def _payload() -> ManufacturingPredictionSnapshotCreate:
    return ManufacturingPredictionSnapshotCreate(
        prediction_type="equipment_risk",
        scope_type="equipment",
        scope_name="水泥磨",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 7),
        forecast_horizon_days=7,
        algorithm_version="deterministic-v1",
        risk_level="中风险",
        data_snapshot={"recent_readings": [{"temperature": 78.0, "vibration": 4.5}]},
        prediction_result={"predicted_risk_level": "中风险", "maintenance_window": "3 个工作日内"},
        ai_mode="rule_based",
        ai_summary="预测结果基于已保存的设备历史数据。",
        generated_at=datetime(2026, 8, 7, 10, 32, tzinfo=timezone.utc),
    )


def test_prediction_snapshot_model_is_registered_and_persists_metadata(db: Session, user: User) -> None:
    service = ManufacturingPredictionService()

    created = service.save_prediction_snapshot(db, user.id, _payload())

    assert created["id"] is not None
    assert created["prediction_type"] == "equipment_risk"
    assert created["scope_name"] == "水泥磨"
    assert created["forecast_horizon_days"] == 7


def test_prediction_service_deep_copies_json_snapshot_before_persisting(db: Session, user: User) -> None:
    service = ManufacturingPredictionService()
    payload = _payload()

    created = service.save_prediction_snapshot(db, user.id, payload)
    payload.data_snapshot["recent_readings"][0]["temperature"] = 0
    payload.prediction_result["predicted_risk_level"] = "正常"

    detail = service.get_prediction_detail(db, user.id, created["id"])

    assert detail is not None
    assert detail["data_snapshot"]["recent_readings"][0]["temperature"] == 78.0
    assert detail["prediction_result"]["predicted_risk_level"] == "中风险"


def test_prediction_service_returns_no_detail_to_a_different_user(db: Session, user: User) -> None:
    service = ManufacturingPredictionService()
    created = service.save_prediction_snapshot(db, user.id, _payload())

    assert service.get_prediction_detail(db, user.id + 1, created["id"]) is None


def test_prediction_migration_declares_history_indexes() -> None:
    migration = Path(__file__).resolve().parents[1] / "sql" / "009_create_manufacturing_prediction_runs.sql"

    content = migration.read_text(encoding="utf-8").lower()

    assert "create table if not exists manufacturing_prediction_runs" in content
    assert "data_snapshot json not null" in content
    assert "prediction_result json not null" in content
    assert "idx_manufacturing_prediction_runs_user_generated" in content
    assert "idx_manufacturing_prediction_runs_scope_generated" in content
