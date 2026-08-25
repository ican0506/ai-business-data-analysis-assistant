import json
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.manufacturing import EnergyRecord, EquipmentRecord, ProductionRecord
from app.models.manufacturing_prediction import ManufacturingPredictionRun
from app.schemas.manufacturing_prediction import ManufacturingPredictionSnapshotCreate
from app.services.prediction_explanation_service import PredictionExplanationService
from app.services.predictors.energy_consumption_predictor import EnergyConsumptionPredictor
from app.services.predictors.equipment_failure_predictor import EquipmentFailurePredictor
from app.services.predictors.production_completion_predictor import ProductionCompletionPredictor


class ManufacturingPredictionService:
    """Persistence boundary for immutable manufacturing prediction snapshots."""

    def generate_prediction(
        self,
        db: Session,
        user_id: int,
        *,
        prediction_type: str,
        scope_name: str | None = None,
        forecast_horizon_days: int = 7,
        target_date: date | None = None,
    ) -> dict:
        """Read manufacturing history, run deterministic predictors and persist one snapshot."""
        equipment_records = self._equipment_records(db, scope_name if prediction_type == "equipment_risk" else None)
        energy_records = self._energy_records(db, scope_name if prediction_type == "energy_consumption" else None)
        production_records = self._production_records(
            db,
            scope_name if prediction_type == "production_completion" else None,
        )

        equipment_predictions = self._equipment_predictions(equipment_records)
        energy_prediction = EnergyConsumptionPredictor().predict(energy_records)
        production_prediction = ProductionCompletionPredictor().predict(
            production_records,
            target_date=target_date,
        )
        prediction_result = {
            "equipment_predictions": equipment_predictions,
            "energy_prediction": energy_prediction,
            "production_prediction": production_prediction,
        }
        data_snapshot = {
            "equipment_data_summary": self._data_summary(
                equipment_records,
                entity_key="equipment_name",
                entity_label="equipment_count",
            ),
            "energy_data_summary": self._data_summary(
                energy_records,
                entity_key="production_line",
                entity_label="production_line_count",
            ),
            "production_data_summary": self._data_summary(
                production_records,
                entity_key="production_line",
                entity_label="production_line_count",
            ),
        }
        risk_level = self._risk_level(prediction_type, prediction_result)
        explanation = PredictionExplanationService().explain(
            prediction_result=prediction_result,
            data_snapshot=data_snapshot,
            risk_level=risk_level,
        )
        data_snapshot["prediction_explanation"] = explanation
        payload = ManufacturingPredictionSnapshotCreate(
            prediction_type=prediction_type,
            scope_type=self._scope_type(prediction_type, scope_name),
            scope_name=scope_name,
            period_start=self._period_boundary(data_snapshot, first=True),
            period_end=self._period_boundary(data_snapshot, first=False),
            forecast_horizon_days=forecast_horizon_days,
            algorithm_version="deterministic-v1",
            risk_level=risk_level,
            data_snapshot=data_snapshot,
            prediction_result=prediction_result,
            ai_mode=explanation["mode"],
            ai_summary=explanation["summary"],
            generated_at=datetime.now(timezone.utc),
        )
        return self.save_prediction_snapshot(db, user_id, payload)

    def save_prediction_snapshot(
        self,
        db: Session,
        user_id: int,
        payload: ManufacturingPredictionSnapshotCreate,
    ) -> dict:
        values = payload.model_dump()
        values["data_snapshot"] = self._json_copy(values["data_snapshot"])
        values["prediction_result"] = self._json_copy(values["prediction_result"])
        prediction = ManufacturingPredictionRun(user_id=user_id, **values)
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        return self.serialize(prediction)

    def get_prediction_detail(
        self,
        db: Session,
        user_id: int,
        prediction_id: int,
    ) -> dict | None:
        prediction = db.scalars(
            select(ManufacturingPredictionRun).where(
                ManufacturingPredictionRun.id == prediction_id,
                ManufacturingPredictionRun.user_id == user_id,
            )
        ).first()
        return self.serialize(prediction) if prediction else None

    def list_for_user(
        self,
        db: Session,
        user_id: int,
        *,
        page: int,
        page_size: int,
        prediction_type: str | None = None,
        scope_name: str | None = None,
    ) -> dict:
        """Return one user's immutable prediction history with deterministic paging."""
        filters = [ManufacturingPredictionRun.user_id == user_id]
        if prediction_type:
            filters.append(ManufacturingPredictionRun.prediction_type == prediction_type)
        if scope_name:
            filters.append(ManufacturingPredictionRun.scope_name == scope_name)
        total = db.scalar(
            select(func.count()).select_from(ManufacturingPredictionRun).where(*filters)
        ) or 0
        predictions = db.scalars(
            select(ManufacturingPredictionRun)
            .where(*filters)
            .order_by(
                ManufacturingPredictionRun.generated_at.desc(),
                ManufacturingPredictionRun.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return {
            "items": [self.serialize(prediction) for prediction in predictions],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def _equipment_records(db: Session, equipment_name: str | None) -> list[dict]:
        statement = select(EquipmentRecord).order_by(EquipmentRecord.date, EquipmentRecord.id)
        if equipment_name:
            statement = statement.where(EquipmentRecord.equipment_name == equipment_name)
        return [
            {
                "equipment_name": record.equipment_name,
                "record_date": record.date,
                "temperature": record.temperature,
                "vibration": record.vibration,
                "fault_count": record.fault_count,
                "status": record.status,
            }
            for record in db.scalars(statement).all()
        ]

    @staticmethod
    def _energy_records(db: Session, production_line: str | None) -> list[dict]:
        statement = select(EnergyRecord).order_by(EnergyRecord.date, EnergyRecord.id)
        if production_line:
            statement = statement.where(EnergyRecord.production_line == production_line)
        return [
            {
                "production_line": record.production_line,
                "record_date": record.date,
                "electricity_consumption": record.electricity_consumption,
                "coal_consumption": record.coal_consumption,
                "unit_energy_consumption": record.unit_energy_consumption,
            }
            for record in db.scalars(statement).all()
        ]

    @staticmethod
    def _production_records(db: Session, production_line: str | None) -> list[dict]:
        statement = select(ProductionRecord).order_by(ProductionRecord.date, ProductionRecord.id)
        if production_line:
            statement = statement.where(ProductionRecord.production_line == production_line)
        return [
            {
                "production_line": record.production_line,
                "record_date": record.date,
                "cement_output": record.cement_output,
                "planned_output": record.planned_output,
            }
            for record in db.scalars(statement).all()
        ]

    @staticmethod
    def _equipment_predictions(records: list[dict]) -> list[dict]:
        grouped: dict[str | None, list[dict]] = {}
        for record in records:
            grouped.setdefault(record.get("equipment_name"), []).append(record)
        if not grouped:
            return [EquipmentFailurePredictor().predict([])]
        return [EquipmentFailurePredictor().predict(grouped[name]) for name in sorted(grouped, key=lambda value: value or "")]

    @staticmethod
    def _data_summary(records: list[dict], *, entity_key: str, entity_label: str) -> dict:
        dates = [record.get("record_date") for record in records if isinstance(record.get("record_date"), date)]
        return {
            "record_count": len(records),
            entity_label: len({record.get(entity_key) for record in records if record.get(entity_key)}),
            "period_start": min(dates).isoformat() if dates else None,
            "period_end": max(dates).isoformat() if dates else None,
        }

    @staticmethod
    def _period_boundary(snapshot: dict, *, first: bool) -> date | None:
        key = "period_start" if first else "period_end"
        values = [
            summary[key]
            for summary in snapshot.values()
            if summary.get(key) is not None
        ]
        return date.fromisoformat(min(values) if first else max(values)) if values else None

    @staticmethod
    def _scope_type(prediction_type: str, scope_name: str | None) -> str:
        if prediction_type == "equipment_risk":
            return "equipment"
        return "production_line" if scope_name else "factory"

    @staticmethod
    def _risk_level(prediction_type: str, result: dict) -> str:
        if prediction_type == "equipment_risk":
            levels = [item["risk_level"] for item in result["equipment_predictions"]]
            priority = {"数据不足": 0, "正常": 1, "中风险": 2, "高风险": 3}
            return max(levels, key=lambda level: priority[level])
        if prediction_type == "energy_consumption":
            return result["energy_prediction"]["warning_level"]
        production = result["production_prediction"]
        if production["trend"] == "数据不足":
            return "数据不足"
        return "高风险" if production["delay_risk"] == "可能延期" else "正常"

    @staticmethod
    def _json_copy(value: dict) -> dict:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))

    @staticmethod
    def serialize(prediction: ManufacturingPredictionRun) -> dict:
        return {
            "id": prediction.id,
            "user_id": prediction.user_id,
            "prediction_type": prediction.prediction_type,
            "scope_type": prediction.scope_type,
            "scope_name": prediction.scope_name,
            "period_start": prediction.period_start.isoformat() if prediction.period_start else None,
            "period_end": prediction.period_end.isoformat() if prediction.period_end else None,
            "forecast_horizon_days": prediction.forecast_horizon_days,
            "algorithm_version": prediction.algorithm_version,
            "risk_level": prediction.risk_level,
            "data_snapshot": ManufacturingPredictionService._json_copy(prediction.data_snapshot),
            "prediction_result": ManufacturingPredictionService._json_copy(prediction.prediction_result),
            "ai_mode": prediction.ai_mode,
            "ai_summary": prediction.ai_summary,
            "generated_at": prediction.generated_at.isoformat(),
            "created_at": prediction.created_at.isoformat(),
        }
