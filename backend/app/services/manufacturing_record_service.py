from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.manufacturing import EnergyRecord, EquipmentRecord, ProductionRecord
from app.schemas.manufacturing import EnergyRecordCreate, EquipmentRecordCreate, ProductionRecordCreate


class ManufacturingRecordService:
    """Manufacturing demo records' persistence and serialization boundary."""

    def create_production(self, db: Session, payload: ProductionRecordCreate) -> dict:
        record = ProductionRecord(**payload.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return self.serialize_production(record)

    def list_production(self, db: Session) -> list[dict]:
        rows = db.scalars(select(ProductionRecord).order_by(ProductionRecord.date.desc(), ProductionRecord.id.desc())).all()
        return [self.serialize_production(row) for row in rows]

    def get_production(self, db: Session, record_id: int) -> dict | None:
        record = db.get(ProductionRecord, record_id)
        return self.serialize_production(record) if record else None

    def create_equipment(self, db: Session, payload: EquipmentRecordCreate) -> dict:
        record = EquipmentRecord(**payload.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return self.serialize_equipment(record)

    def list_equipment(self, db: Session) -> list[dict]:
        rows = db.scalars(select(EquipmentRecord).order_by(EquipmentRecord.date.desc(), EquipmentRecord.id.desc())).all()
        return [self.serialize_equipment(row) for row in rows]

    def get_equipment(self, db: Session, record_id: int) -> dict | None:
        record = db.get(EquipmentRecord, record_id)
        return self.serialize_equipment(record) if record else None

    def create_energy(self, db: Session, payload: EnergyRecordCreate) -> dict:
        record = EnergyRecord(**payload.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return self.serialize_energy(record)

    def list_energy(self, db: Session) -> list[dict]:
        rows = db.scalars(select(EnergyRecord).order_by(EnergyRecord.date.desc(), EnergyRecord.id.desc())).all()
        return [self.serialize_energy(row) for row in rows]

    def get_energy(self, db: Session, record_id: int) -> dict | None:
        record = db.get(EnergyRecord, record_id)
        return self.serialize_energy(record) if record else None

    @staticmethod
    def serialize_production(record: ProductionRecord) -> dict:
        return {
            "id": record.id,
            "date": record.date.isoformat(),
            "production_line": record.production_line,
            "clinker_output": float(record.clinker_output),
            "cement_output": float(record.cement_output),
            "planned_output": float(record.planned_output),
            "completion_rate": float(record.completion_rate),
            "running_hours": float(record.running_hours),
            "downtime_hours": float(record.downtime_hours),
        }

    @staticmethod
    def serialize_equipment(record: EquipmentRecord) -> dict:
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

    @staticmethod
    def serialize_energy(record: EnergyRecord) -> dict:
        return {
            "id": record.id,
            "date": record.date.isoformat(),
            "production_line": record.production_line,
            "electricity_consumption": float(record.electricity_consumption),
            "coal_consumption": float(record.coal_consumption),
            "unit_energy_consumption": float(record.unit_energy_consumption),
        }
