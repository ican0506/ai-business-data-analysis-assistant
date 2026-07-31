import io
import json
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.dataset import Dataset, DatasetColumn


class DatasetService:
    allowed_extensions = {".csv", ".xlsx"}

    def create_from_upload(self, db: Session, owner_id: int, upload: UploadFile, content: bytes) -> dict:
        original_filename = upload.filename or ""
        suffix = Path(original_filename).suffix.lower()
        if suffix not in self.allowed_extensions:
            raise ValueError("仅支持 CSV 或 XLSX 文件")

        settings = get_settings()
        max_file_size = settings.upload_max_file_size_mb * 1024 * 1024
        if not content:
            raise ValueError("上传文件不能为空")
        if len(content) > max_file_size:
            raise ValueError(f"文件不能超过 {settings.upload_max_file_size_mb} MB")

        storage_path = Path("uploads") / str(owner_id) / f"{uuid4().hex}{suffix}"
        absolute_path = settings.resolved_storage_root / storage_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)

        try:
            frame = self._read_dataframe(content, suffix)
            columns = self._build_columns(frame)
            dataset = Dataset(
                owner_id=owner_id,
                original_filename=original_filename,
                storage_path=storage_path.as_posix(),
                file_type=suffix.lstrip("."),
                file_size=len(content),
                status="UPLOADED",
                row_count=len(frame.index),
                column_count=len(frame.columns),
            )
            db.add(dataset)
            db.flush()
            db.add_all(
                DatasetColumn(dataset_id=dataset.id, **column)
                for column in columns
            )
            db.commit()
            db.refresh(dataset)
        except Exception:
            db.rollback()
            absolute_path.unlink(missing_ok=True)
            raise

        return {
            "id": dataset.id,
            "original_filename": dataset.original_filename,
            "file_type": dataset.file_type,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "status": dataset.status,
            "columns": [{"name": column["name"], "data_type": column["data_type"], "missing_count": column["missing_count"], "unique_count": column["unique_count"]} for column in columns],
            "preview": self._build_preview(frame),
        }

    @staticmethod
    def _read_dataframe(content: bytes, suffix: str) -> pd.DataFrame:
        if suffix == ".xlsx":
            return pd.read_excel(io.BytesIO(content))

        last_error: UnicodeDecodeError | None = None
        for encoding in ("utf-8-sig", "utf-8", "gbk"):
            try:
                return pd.read_csv(io.BytesIO(content), encoding=encoding)
            except UnicodeDecodeError as error:
                last_error = error
        raise ValueError("CSV 文件编码无法识别") from last_error

    @staticmethod
    def _build_columns(frame: pd.DataFrame) -> list[dict]:
        columns: list[dict] = []
        for position, name in enumerate(frame.columns):
            series = frame[name]
            columns.append(
                {
                    "name": str(name),
                    "data_type": DatasetService._infer_data_type(series),
                    "position": position,
                    "missing_count": int(series.isna().sum()),
                    "unique_count": int(series.nunique(dropna=True)),
                }
            )
        return columns

    @staticmethod
    def _infer_data_type(series: pd.Series) -> str:
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        if pd.api.types.is_numeric_dtype(series):
            return "number"
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        return "text"

    @staticmethod
    def _build_preview(frame: pd.DataFrame) -> list[dict]:
        preview_json = frame.head(20).to_json(orient="records", force_ascii=False, date_format="iso")
        return json.loads(preview_json)
