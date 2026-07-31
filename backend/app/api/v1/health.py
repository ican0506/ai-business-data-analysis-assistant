from fastapi import APIRouter

from app.db.session import is_database_available
from app.services.health_service import build_health_payload


router = APIRouter(prefix="/api/v1", tags=["系统"])


@router.get("/health")
def health_check() -> dict[str, object]:
    return {
        "code": 0,
        "message": "success",
        "data": build_health_payload(is_database_available),
    }
