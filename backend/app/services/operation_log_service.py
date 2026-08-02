from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.operation_log import OperationLog


class OperationLogService:
    def record(self, db: Session, user_id: int, action: str, target_type: str, target_id: int | None, detail: str = "") -> None:
        db.add(OperationLog(user_id=user_id, action=action, target_type=target_type, target_id=target_id, detail=detail[:500]))
        db.commit()

    def list_paginated(self, db: Session, page: int, page_size: int) -> dict:
        total = db.scalar(select(func.count()).select_from(OperationLog)) or 0
        rows = db.scalars(
            select(OperationLog)
            .order_by(OperationLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        items = [
            {
                "id": row.id,
                "user_id": row.user_id,
                "action": row.action,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "detail": row.detail,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }
