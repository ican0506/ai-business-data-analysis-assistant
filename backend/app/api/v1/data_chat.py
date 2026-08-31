from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.data_chat import DataChatQueryRequest
from app.services.data_chat.data_chat_service import DataChatService, DataChatServiceError
from app.services.operation_log_service import OperationLogService


router = APIRouter(prefix="/api/v1/data-chat", tags=["AI 数据问答"])
service = DataChatService()
operation_log_service = OperationLogService()


@router.post("/query")
def query_data_chat(
    request: DataChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        data = service.query(db, current_user, request.dataset_id, request.question.strip())
    except DataChatServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    operation_log_service.record(db, current_user.id, "DATA_CHAT_QUERY", "dataset", request.dataset_id)
    return {"code": 0, "message": "查询成功", "data": data}
