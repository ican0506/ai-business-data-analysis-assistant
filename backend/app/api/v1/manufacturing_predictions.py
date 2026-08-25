from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.manufacturing_prediction import (
    ManufacturingPredictionCreateRequest,
    PredictionType,
)
from app.services.manufacturing_prediction_service import ManufacturingPredictionService


router = APIRouter(prefix="/api/v1/manufacturing-predictions", tags=["制造业预测"])
service = ManufacturingPredictionService()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_manufacturing_predictions(
    payload: ManufacturingPredictionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    predictions = [
        service.generate_prediction(
            db,
            current_user.id,
            prediction_type=prediction_type,
            scope_name=(
                payload.equipment_name
                if prediction_type == "equipment_risk"
                else payload.production_line
            ),
            forecast_horizon_days=payload.forecast_horizon_days,
        )
        for prediction_type in payload.prediction_types
    ]
    primary = predictions[0]
    return {
        "code": 0,
        "message": "预测生成成功",
        "data": {
            "id": primary["id"],
            "prediction_result": primary["prediction_result"],
            "risk_level": primary["risk_level"],
            "items": predictions,
            "total": len(predictions),
        },
    }


@router.get("")
def list_manufacturing_predictions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    prediction_type: PredictionType | None = None,
    scope_name: str | None = Query(default=None, min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return {
        "code": 0,
        "message": "预测历史读取成功",
        "data": service.list_for_user(
            db,
            current_user.id,
            page=page,
            page_size=page_size,
            prediction_type=prediction_type,
            scope_name=scope_name,
        ),
    }


@router.get("/{prediction_id}")
def get_manufacturing_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    prediction = service.get_prediction_detail(db, current_user.id, prediction_id)
    if prediction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预测记录不存在")
    return {"code": 0, "message": "预测详情读取成功", "data": prediction}
