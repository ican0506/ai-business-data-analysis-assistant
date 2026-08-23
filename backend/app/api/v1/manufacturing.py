from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.manufacturing import EnergyRecordCreate, EquipmentRecordCreate, ProductionRecordCreate
from app.services.manufacturing_record_service import ManufacturingRecordService
from app.services.operation_log_service import OperationLogService


router = APIRouter(tags=["制造业数据"])
service = ManufacturingRecordService()
operation_log_service = OperationLogService()


def _list_response(items: list[dict], message: str) -> dict:
    return {"code": 0, "message": message, "data": {"items": items, "total": len(items)}}


@router.post("/api/v1/production-records", status_code=status.HTTP_201_CREATED)
def create_production_record(
    payload: ProductionRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = service.create_production(db, payload)
    operation_log_service.record(db, current_user.id, "PRODUCTION_RECORD_CREATE", "production_record", data["id"])
    return {"code": 0, "message": "生产记录创建成功", "data": data}


@router.get("/api/v1/production-records")
def list_production_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return _list_response(service.list_production(db), "生产记录读取成功")


@router.get("/api/v1/production-records/{record_id}")
def get_production_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = service.get_production(db, record_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生产记录不存在")
    return {"code": 0, "message": "生产记录读取成功", "data": data}


@router.post("/api/v1/equipment-records", status_code=status.HTTP_201_CREATED)
def create_equipment_record(
    payload: EquipmentRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = service.create_equipment(db, payload)
    operation_log_service.record(db, current_user.id, "EQUIPMENT_RECORD_CREATE", "equipment_record", data["id"])
    return {"code": 0, "message": "设备运行记录创建成功", "data": data}


@router.get("/api/v1/equipment-records")
def list_equipment_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return _list_response(service.list_equipment(db), "设备运行记录读取成功")


@router.get("/api/v1/equipment-records/{record_id}")
def get_equipment_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = service.get_equipment(db, record_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备运行记录不存在")
    return {"code": 0, "message": "设备运行记录读取成功", "data": data}


@router.post("/api/v1/energy-records", status_code=status.HTTP_201_CREATED)
def create_energy_record(
    payload: EnergyRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = service.create_energy(db, payload)
    operation_log_service.record(db, current_user.id, "ENERGY_RECORD_CREATE", "energy_record", data["id"])
    return {"code": 0, "message": "能源消耗记录创建成功", "data": data}


@router.get("/api/v1/energy-records")
def list_energy_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return _list_response(service.list_energy(db), "能源消耗记录读取成功")


@router.get("/api/v1/energy-records/{record_id}")
def get_energy_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = service.get_energy(db, record_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="能源消耗记录不存在")
    return {"code": 0, "message": "能源消耗记录读取成功", "data": data}
