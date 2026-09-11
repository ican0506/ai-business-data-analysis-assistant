from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.manufacturing import EquipmentRecord
from app.services.moonbit_service import MoonBitService


class EquipmentManagementService:
    """Builds deterministic equipment views from persisted equipment records."""

    TEMPERATURE_THRESHOLD = 80.0
    VIBRATION_THRESHOLD = 5.0
    RUNNING_STATUS = "运行"

    def list_latest(self, db: Session) -> list[dict]:
        return [self.serialize(record) for record in self._latest_records(db)]

    def get_latest(self, db: Session, equipment_name: str) -> dict | None:
        record = db.scalars(
            select(EquipmentRecord)
            .where(EquipmentRecord.equipment_name == equipment_name)
            .order_by(EquipmentRecord.date.desc(), EquipmentRecord.id.desc())
        ).first()
        return self.serialize(record) if record else None

    def get_history(self, db: Session, equipment_name: str) -> list[dict]:
        records = db.scalars(
            select(EquipmentRecord)
            .where(EquipmentRecord.equipment_name == equipment_name)
            .order_by(EquipmentRecord.date.asc(), EquipmentRecord.id.asc())
        ).all()
        return [self.serialize(record) for record in records]

    def analyze_anomalies(self, db: Session) -> list[dict]:
        alerts: list[dict] = []
        for record in self._latest_records(db):
            alerts.extend(self._alerts_for_record(record))
        return alerts

    def _latest_records(self, db: Session) -> list[EquipmentRecord]:
        rows = db.scalars(
            select(EquipmentRecord).order_by(EquipmentRecord.date.desc(), EquipmentRecord.id.desc())
        ).all()
        latest_by_name: dict[str, EquipmentRecord] = {}
        for record in rows:
            latest_by_name.setdefault(record.equipment_name, record)
        return [latest_by_name[name] for name in sorted(latest_by_name)]

    def _alerts_for_record(self, record: EquipmentRecord) -> list[dict]:
        moonbit_risk = MoonBitService().evaluate_equipment_risk(
            temperature=float(record.temperature),
            vibration=float(record.vibration),
            fault_count=record.fault_count,
            status=record.status,
        )
        if moonbit_risk is not None:
            return [self._alert_for_rule(record, rule_id) for rule_id in moonbit_risk["triggered_rules"]]

        alerts: list[dict] = []
        if record.fault_count > 0:
            alerts.append(self._alert_for_rule(record, "fault_count"))
        if record.status != self.RUNNING_STATUS:
            alerts.append(self._alert_for_rule(record, "status"))
        if float(record.temperature) >= self.TEMPERATURE_THRESHOLD:
            alerts.append(self._alert_for_rule(record, "temperature"))
        if float(record.vibration) >= self.VIBRATION_THRESHOLD:
            alerts.append(self._alert_for_rule(record, "vibration"))
        return alerts

    def _alert_for_rule(self, record: EquipmentRecord, rule_id: str) -> dict:
        if rule_id == "fault_count":
            return self._alert(record, rule_id, "高", f"故障次数为 {record.fault_count} 次", record.fault_count)
        if rule_id == "status":
            return self._alert(record, rule_id, "中", f"设备状态为“{record.status}”", record.status)
        if rule_id == "temperature":
            return self._alert(
                record,
                rule_id,
                "高",
                f"温度达到 {float(record.temperature):.1f}℃",
                float(record.temperature),
                self.TEMPERATURE_THRESHOLD,
            )
        return self._alert(
            record,
            "vibration",
            "高",
            f"振动值达到 {float(record.vibration):.3f}",
            float(record.vibration),
            self.VIBRATION_THRESHOLD,
        )

    def _alert(
        self,
        record: EquipmentRecord,
        rule_id: str,
        severity: str,
        message: str,
        observed_value: float | int | str,
        threshold: float | None = None,
    ) -> dict:
        return {
            "equipment_name": record.equipment_name,
            "date": record.date.isoformat(),
            "rule_id": rule_id,
            "severity": severity,
            "message": message,
            "observed_value": observed_value,
            "threshold": threshold,
        }

    @staticmethod
    def serialize(record: EquipmentRecord) -> dict:
        return {
            "id": record.id,
            "date": record.date.isoformat(),
            "equipment_name": record.equipment_name,
            "status": record.status,
            "running_hours": float(record.running_hours),
            "fault_count": record.fault_count,
            "temperature": float(record.temperature),
            "vibration": float(record.vibration),
        }
