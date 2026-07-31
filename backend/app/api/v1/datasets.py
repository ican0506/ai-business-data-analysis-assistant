from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.services.data_cleaning_service import DataCleaningService
from app.services.dataset_service import DatasetService
from app.services.metrics_service import MetricsService


router = APIRouter(prefix="/api/v1/datasets", tags=["数据集"])
service = DatasetService()
cleaning_service = DataCleaningService()
metrics_service = MetricsService()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        data = service.create_from_upload(db, current_user.id, file, await file.read())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="文件解析失败，请检查文件内容") from error
    return {"code": 0, "message": "上传并解析成功", "data": data}


@router.post("/{dataset_id}/clean", status_code=status.HTTP_201_CREATED)
def clean_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据集不存在")
    if dataset.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权清洗此数据集")

    try:
        data = cleaning_service.clean_dataset(db, dataset)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="数据清洗失败，请检查文件内容") from error
    return {"code": 0, "message": "数据清洗成功", "data": data}


@router.get("/{dataset_id}/metrics")
def get_dataset_metrics(dataset_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据集不存在")
    if dataset.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此数据集")
    try:
        data = metrics_service.build_metrics(db, dataset)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return {"code": 0, "message": "统计分析成功", "data": data}
