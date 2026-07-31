from pathlib import Path
from uuid import uuid4

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.models.dataset_cleaning import DatasetCleaningRun
from app.services.dataset_service import DatasetService


class DataCleaningService:
    field_aliases = {
        "date": {"date", "日期", "日期时间", "交易日期"},
        "region": {"region", "区域", "大区"},
        "product": {"product", "产品", "商品"},
        "sales_amount": {"sales_amount", "sales", "销售额", "销售金额"},
        "target_amount": {"target_amount", "target", "目标额", "目标金额"},
        "customer_count": {"customer_count", "customers", "客户数"},
    }
    numeric_columns = {"sales_amount", "target_amount", "customer_count"}

    def clean_dataset(self, db: Session, dataset: Dataset) -> dict:
        settings = get_settings()
        source_path = settings.resolved_storage_root / dataset.storage_path
        if not source_path.is_file():
            raise ValueError("原始上传文件不存在，无法执行清洗")

        frame = DatasetService._read_dataframe(source_path.read_bytes(), f".{dataset.file_type}")
        original_row_count = len(frame.index)
        frame = self._standardize_column_names(frame)
        frame, removed_empty_rows, removed_duplicate_rows = self._remove_invalid_rows(frame)
        frame, invalid_value_count = self._standardize_values(frame)
        missing_value_count = int(frame.isna().sum().sum())

        cleaned_storage_path = Path("cleaned") / str(dataset.id) / f"{uuid4().hex}.csv"
        absolute_cleaned_path = settings.resolved_storage_root / cleaned_storage_path
        absolute_cleaned_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(absolute_cleaned_path, index=False, encoding="utf-8-sig")

        try:
            run = DatasetCleaningRun(
                dataset_id=dataset.id,
                cleaned_storage_path=cleaned_storage_path.as_posix(),
                original_row_count=original_row_count,
                cleaned_row_count=len(frame.index),
                removed_empty_rows=removed_empty_rows,
                removed_duplicate_rows=removed_duplicate_rows,
                invalid_value_count=invalid_value_count,
                missing_value_count=missing_value_count,
            )
            dataset.status = "CLEANED"
            db.add(run)
            db.commit()
            db.refresh(run)
        except Exception:
            db.rollback()
            absolute_cleaned_path.unlink(missing_ok=True)
            raise

        return {
            "cleaning_run_id": run.id,
            "dataset_id": dataset.id,
            "status": dataset.status,
            "original_row_count": run.original_row_count,
            "cleaned_row_count": run.cleaned_row_count,
            "removed_empty_rows": run.removed_empty_rows,
            "removed_duplicate_rows": run.removed_duplicate_rows,
            "invalid_value_count": run.invalid_value_count,
            "missing_value_count": run.missing_value_count,
            "columns": [str(column) for column in frame.columns],
            "preview": DatasetService._build_preview(frame),
        }

    def _standardize_column_names(self, frame: pd.DataFrame) -> pd.DataFrame:
        aliases = {
            self._normalize_name(alias): standard_name
            for standard_name, values in self.field_aliases.items()
            for alias in values
        }
        standardized_columns = [aliases.get(self._normalize_name(column), str(column).strip()) for column in frame.columns]
        result = frame.copy()
        result.columns = standardized_columns
        if result.columns.duplicated().any():
            result = result.T.groupby(level=0, sort=False).first().T
        return result

    @staticmethod
    def _normalize_name(name: object) -> str:
        return "".join(str(name).strip().lower().split())

    @staticmethod
    def _remove_invalid_rows(frame: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
        after_empty = frame.dropna(how="all")
        removed_empty_rows = len(frame.index) - len(after_empty.index)
        cleaned = after_empty.drop_duplicates()
        removed_duplicate_rows = len(after_empty.index) - len(cleaned.index)
        return cleaned, removed_empty_rows, removed_duplicate_rows

    def _standardize_values(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        result = frame.copy()
        invalid_value_count = 0

        if "date" in result.columns:
            source = result["date"]
            parsed = pd.to_datetime(source, errors="coerce")
            invalid_value_count += int((source.notna() & parsed.isna()).sum())
            result["date"] = parsed.dt.strftime("%Y-%m-%d")

        for column in self.numeric_columns.intersection(result.columns):
            source = result[column]
            normalized = source.astype("string").str.replace(",", "", regex=False).str.replace("¥", "", regex=False).str.strip()
            parsed = pd.to_numeric(normalized, errors="coerce")
            invalid_value_count += int((source.notna() & parsed.isna()).sum())
            result[column] = parsed

        return result, invalid_value_count
