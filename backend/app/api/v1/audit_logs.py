from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.operation_log_service import OperationLogService


router = APIRouter(prefix="/api/v1/audit-logs", tags=["操作日志"])
service = OperationLogService()


@router.get("")
def list_audit_logs(
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量，最大 100"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可以查看操作日志")
    return {"code": 0, "message": "查询成功", "data": service.list_paginated(db, page, page_size)}
