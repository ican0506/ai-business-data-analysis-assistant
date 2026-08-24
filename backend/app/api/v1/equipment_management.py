from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.equipment_management_service import EquipmentManagementService


router = APIRouter(prefix="/api/v1/equipment-management", tags=["设备管理"])
service = EquipmentManagementService()


@router.get("")
def list_equipment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = service.list_latest(db)
    return {"code": 0, "message": "设备列表读取成功", "data": {"items": items, "total": len(items)}}


@router.get("/anomalies")
def list_equipment_anomalies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = service.analyze_anomalies(db)
    return {"code": 0, "message": "设备异常分析完成", "data": {"items": items, "total": len(items)}}


@router.get("/{equipment_name}")
def get_equipment_detail(
    equipment_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = service.get_latest(db, equipment_name)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    return {"code": 0, "message": "设备详情读取成功", "data": data}


@router.get("/{equipment_name}/history")
def get_equipment_history(
    equipment_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = service.get_history(db, equipment_name)
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    return {"code": 0, "message": "设备历史运行记录读取成功", "data": {"equipment_name": equipment_name, "items": items, "total": len(items)}}
