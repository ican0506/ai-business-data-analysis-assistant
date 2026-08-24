from collections.abc import Generator
from datetime import date, datetime, timezone
from types import SimpleNamespace
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import create_app
from app.models.manufacturing import EnergyRecord, EquipmentRecord, ProductionRecord
from app.models.manufacturing_business_report import ManufacturingBusinessReport
from app.models.user import Base, User
from app.schemas.manufacturing_business_report import ManufacturingBusinessReportSnapshotCreate
from app.services.manufacturing_business_report_service import ManufacturingBusinessReportService


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def user(db: Session) -> User:
    user = User(username="report_owner", email="report@example.com", password_hash="not-used")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _payload() -> ManufacturingBusinessReportSnapshotCreate:
    return ManufacturingBusinessReportSnapshotCreate(
        title="2026 年第 31 周生产经营分析报告",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 7),
        risk_level="中风险",
        ai_mode="rule_based",
        summary="生产总体稳定，建议优先处理设备风险。",
        snapshot={"kpis": {"cement_output": 6500}, "equipment_diagnoses": []},
        generated_at=datetime(2026, 8, 7, 10, 32, tzinfo=timezone.utc),
    )


def test_report_snapshot_model_persists_json_and_generation_metadata(db: Session, user: User) -> None:
    payload = _payload()
    report = ManufacturingBusinessReport(user_id=user.id, **payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)

    assert report.id is not None
    assert report.snapshot["kpis"]["cement_output"] == 6500
    assert report.period_start == date(2026, 8, 1)
    assert report.generated_at == datetime(2026, 8, 7, 10, 32)


def test_service_creates_and_reads_an_isolated_snapshot(db: Session, user: User) -> None:
    service = ManufacturingBusinessReportService()
    payload = _payload()

    created = service.create_snapshot(db, user.id, payload)
    payload.snapshot["kpis"]["cement_output"] = 0
    detail = service.get_detail(db, user.id, created["id"])

    assert detail is not None
    assert detail["summary"] == "生产总体稳定，建议优先处理设备风险。"
    assert detail["snapshot"]["kpis"]["cement_output"] == 6500
    assert service.get_detail(db, user.id + 1, created["id"]) is None


def test_business_report_migration_declares_snapshot_and_history_indexes() -> None:
    migration = Path(__file__).resolve().parents[1] / "sql" / "008_create_manufacturing_business_reports.sql"

    content = migration.read_text(encoding="utf-8").lower()

    assert "create table if not exists manufacturing_business_reports" in content
    assert "snapshot json not null" in content
    assert "idx_manufacturing_business_reports_user_generated" in content


def _seed_operational_records(db: Session) -> None:
    db.add_all(
        [
            ProductionRecord(
                date=date(2026, 8, 1),
                production_line="1号线",
                clinker_output=5000,
                cement_output=6500,
                planned_output=7000,
                completion_rate=0,
                running_hours=22,
                downtime_hours=2,
            ),
            ProductionRecord(
                date=date(2026, 8, 1),
                production_line="2号线",
                clinker_output=4000,
                cement_output=5000,
                planned_output=6000,
                completion_rate=0,
                running_hours=20,
                downtime_hours=4,
            ),
            EquipmentRecord(
                date=date(2026, 8, 1),
                equipment_name="水泥磨",
                status="运行",
                running_hours=22,
                fault_count=0,
                temperature=65,
                vibration=3.2,
            ),
            EquipmentRecord(
                date=date(2026, 8, 2),
                equipment_name="回转窑",
                status="检修",
                running_hours=12,
                fault_count=2,
                temperature=84,
                vibration=5.4,
            ),
            EnergyRecord(
                date=date(2026, 8, 1),
                production_line="1号线",
                electricity_consumption=75,
                coal_consumption=105,
                unit_energy_consumption=75,
            ),
            EnergyRecord(
                date=date(2026, 8, 1),
                production_line="2号线",
                electricity_consumption=80,
                coal_consumption=110,
                unit_energy_consumption=80,
            ),
            EnergyRecord(
                date=date(2026, 8, 2),
                production_line="1号线",
                electricity_consumption=70,
                coal_consumption=100,
                unit_energy_consumption=70,
            ),
        ]
    )
    db.commit()


def test_service_builds_deterministic_production_equipment_and_energy_snapshot(db: Session) -> None:
    _seed_operational_records(db)

    snapshot = ManufacturingBusinessReportService().build_deterministic_snapshot(db)

    assert snapshot["production_analysis"] == {
        "clinker_output_total": 9000.0,
        "cement_output_total": 11500.0,
        "planned_output_total": 13000.0,
        "completion_rate": 88.46,
        "production_line_comparison": [
            {
                "production_line": "1号线",
                "clinker_output": 5000.0,
                "cement_output": 6500.0,
                "planned_output": 7000.0,
                "completion_rate": 92.86,
            },
            {
                "production_line": "2号线",
                "clinker_output": 4000.0,
                "cement_output": 5000.0,
                "planned_output": 6000.0,
                "completion_rate": 83.33,
            },
        ],
    }
    assert snapshot["equipment_analysis"] == {
        "equipment_count": 2,
        "running_rate": 70.83,
        "fault_count": 2,
        "abnormal_equipment_count": 1,
    }
    assert snapshot["energy_analysis"] == {
        "average_unit_energy_consumption": 75.0,
        "electricity_consumption_total": 225.0,
        "coal_consumption_total": 315.0,
        "energy_trend": [
            {
                "date": "2026-08-01",
                "electricity_consumption": 155.0,
                "coal_consumption": 215.0,
                "average_unit_energy_consumption": 77.5,
            },
            {
                "date": "2026-08-02",
                "electricity_consumption": 70.0,
                "coal_consumption": 100.0,
                "average_unit_energy_consumption": 70.0,
            },
        ],
    }


def test_service_persists_deterministic_analysis_sections_inside_snapshot(db: Session, user: User) -> None:
    _seed_operational_records(db)
    service = ManufacturingBusinessReportService()
    deterministic_snapshot = service.build_deterministic_snapshot(db)
    payload = _payload().model_copy(update={"snapshot": deterministic_snapshot})

    created = service.create_snapshot(db, user.id, payload)
    detail = service.get_detail(db, user.id, created["id"])

    assert detail is not None
    assert detail["snapshot"]["production_analysis"]["cement_output_total"] == 11500.0
    assert detail["snapshot"]["equipment_analysis"]["abnormal_equipment_count"] == 1
    assert detail["snapshot"]["energy_analysis"]["energy_trend"][0]["date"] == "2026-08-01"


def test_service_generates_and_persists_rule_based_business_report(
    db: Session, user: User, monkeypatch
) -> None:
    _seed_operational_records(db)
    monkeypatch.setattr(
        "app.services.manufacturing_business_report_service.get_settings",
        lambda: SimpleNamespace(llm_provider="", llm_api_key=""),
    )

    report = ManufacturingBusinessReportService().generate_business_report(
        db, user.id, title="2026 年第 31 周生产经营报告"
    )

    assert report["title"] == "2026 年第 31 周生产经营报告"
    assert report["ai_mode"] == "rule_based"
    assert report["risk_level"] == "高风险"
    assert report["snapshot"]["production_analysis"]["cement_output_total"] == 11500.0
    assert report["snapshot"]["equipment_diagnoses"][1]["equipment_name"] == "水泥磨"
    assert report["snapshot"]["ai_summary"]["suggestions"]
    assert ManufacturingBusinessReportService().get_detail(db, user.id, report["id"]) is not None


@pytest.fixture()
def api_client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        session = testing_session()
        try:
            yield session
        finally:
            session.close()

    app = create_app(create_tables=False)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


def _headers_for(api_client: TestClient, suffix: str) -> dict[str, str]:
    api_client.post(
        "/api/v1/auth/register",
        json={
            "username": f"report_user_{suffix}",
            "email": f"report_{suffix}@example.com",
            "password": "Password123",
        },
    )
    login = api_client.post(
        "/api/v1/auth/login",
        json={"username": f"report_user_{suffix}", "password": "Password123"},
    )
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def _seed_api_operational_records(api_client: TestClient, headers: dict[str, str]) -> None:
    for payload in (
        {
            "date": "2026-08-01",
            "production_line": "1号线",
            "clinker_output": 5000,
            "cement_output": 6500,
            "planned_output": 7000,
            "completion_rate": 0,
            "running_hours": 22,
            "downtime_hours": 2,
        },
    ):
        assert api_client.post("/api/v1/production-records", headers=headers, json=payload).status_code == 201
    assert api_client.post(
        "/api/v1/equipment-records",
        headers=headers,
        json={
            "date": "2026-08-01",
            "equipment_name": "水泥磨",
            "status": "运行",
            "running_hours": 22,
            "fault_count": 0,
            "temperature": 65,
            "vibration": 3.2,
        },
    ).status_code == 201
    assert api_client.post(
        "/api/v1/energy-records",
        headers=headers,
        json={
            "date": "2026-08-01",
            "production_line": "1号线",
            "electricity_consumption": 75,
            "coal_consumption": 105,
            "unit_energy_consumption": 75,
        },
    ).status_code == 201


def test_manufacturing_report_api_creates_lists_reads_and_isolates_reports(
    api_client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.services.manufacturing_business_report_service.get_settings",
        lambda: SimpleNamespace(llm_provider="", llm_api_key=""),
    )
    owner_headers = _headers_for(api_client, "owner")
    other_headers = _headers_for(api_client, "other")
    _seed_api_operational_records(api_client, owner_headers)

    created = api_client.post(
        "/api/v1/manufacturing-reports",
        headers=owner_headers,
        json={"title": "生产经营日报"},
    )

    assert created.status_code == 201
    report = created.json()["data"]
    assert report["snapshot"]["energy_analysis"]["electricity_consumption_total"] == 75.0

    history = api_client.get("/api/v1/manufacturing-reports", headers=owner_headers)
    assert history.status_code == 200
    assert history.json()["data"]["total"] == 1

    detail = api_client.get(
        f"/api/v1/manufacturing-reports/{report['id']}", headers=owner_headers
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == report["id"]

    isolated = api_client.get(
        f"/api/v1/manufacturing-reports/{report['id']}", headers=other_headers
    )
    assert isolated.status_code == 404


@pytest.mark.parametrize(
    ("report_format", "expected_prefix"),
    [("excel", b"PK"), ("word", b"PK"), ("pdf", b"%PDF")],
)
def test_service_exports_only_the_persisted_report_snapshot(
    db: Session, user: User, report_format: str, expected_prefix: bytes
) -> None:
    service = ManufacturingBusinessReportService()
    report = service.create_snapshot(
        db,
        user.id,
        _payload().model_copy(
            update={
                "snapshot": {
                    "production_analysis": {
                        "clinker_output_total": 9000.0,
                        "cement_output_total": 11500.0,
                        "planned_output_total": 13000.0,
                        "completion_rate": 88.46,
                        "production_line_comparison": [],
                    },
                    "equipment_analysis": {
                        "equipment_count": 2,
                        "running_rate": 70.83,
                        "fault_count": 2,
                        "abnormal_equipment_count": 1,
                    },
                    "energy_analysis": {
                        "average_unit_energy_consumption": 75.0,
                        "electricity_consumption_total": 225.0,
                        "coal_consumption_total": 315.0,
                        "energy_trend": [],
                    },
                    "equipment_diagnoses": [],
                    "ai_summary": {"summary": "快照 AI 总结", "suggestions": ["持续跟踪"], "mode": "rule_based"},
                }
            }
        ),
    )

    content = service.build_export(report, report_format)

    assert content.startswith(expected_prefix)
    if report_format == "excel":
        from openpyxl import load_workbook

        workbook = load_workbook(BytesIO(content))
        assert workbook.active["B5"].value == 11500.0


def test_manufacturing_report_export_api_returns_the_requested_snapshot_format(
    api_client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.services.manufacturing_business_report_service.get_settings",
        lambda: SimpleNamespace(llm_provider="", llm_api_key=""),
    )
    headers = _headers_for(api_client, "export")
    _seed_api_operational_records(api_client, headers)
    report_id = api_client.post("/api/v1/manufacturing-reports", headers=headers, json={}).json()["data"]["id"]

    response = api_client.get(
        f"/api/v1/manufacturing-reports/{report_id}/export/pdf", headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")
