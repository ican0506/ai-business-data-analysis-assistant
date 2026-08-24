from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.equipment_diagnosis_service import EquipmentDiagnosisService


router = APIRouter(prefix="/api/v1/equipment-diagnosis", tags=["AI设备诊断"])
service = EquipmentDiagnosisService()


@router.post("/{equipment_name}")
def diagnose_equipment(
    equipment_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    diagnosis = service.diagnose(db, equipment_name)
    if diagnosis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    return {"code": 0, "message": "设备 AI 诊断完成", "data": diagnosis}
