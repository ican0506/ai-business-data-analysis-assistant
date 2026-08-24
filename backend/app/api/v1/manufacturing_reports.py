from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.manufacturing_business_report import ManufacturingBusinessReportGenerateRequest
from app.services.manufacturing_business_report_service import ManufacturingBusinessReportService


router = APIRouter(prefix="/api/v1/manufacturing-reports", tags=["制造业经营报告"])
service = ManufacturingBusinessReportService()


@router.post("", status_code=status.HTTP_201_CREATED)
def generate_manufacturing_report(
    payload: ManufacturingBusinessReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    report = service.generate_business_report(
        db,
        current_user.id,
        title=payload.title,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    return {"code": 0, "message": "制造业经营报告生成成功", "data": report}


@router.get("")
def list_manufacturing_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = service.list_for_user(db, current_user.id)
    return {"code": 0, "message": "制造业经营报告读取成功", "data": {"items": items, "total": len(items)}}


@router.get("/{report_id}")
def get_manufacturing_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    report = service.get_detail(db, current_user.id, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经营报告不存在")
    return {"code": 0, "message": "制造业经营报告读取成功", "data": report}


@router.get("/{report_id}/export/{report_format}")
def export_manufacturing_report(
    report_id: int,
    report_format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    if report_format not in {"excel", "word", "pdf"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告类型不存在")
    report = service.get_detail(db, current_user.id, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经营报告不存在")
    content = service.build_export(report, report_format)
    media_types = {
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
    }
    extensions = {"excel": "xlsx", "word": "docx", "pdf": "pdf"}
    return StreamingResponse(
        BytesIO(content),
        media_type=media_types[report_format],
        headers={"Content-Disposition": f'attachment; filename="manufacturing-report-{report_id}.{extensions[report_format]}"'},
    )
