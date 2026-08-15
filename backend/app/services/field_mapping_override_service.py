from pathlib import Path

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.models.dataset_cleaning import DatasetCleaningRun
from app.models.dataset_field_mapping_override import DatasetFieldMappingOverride
from app.services.canonical_field_mapper import CanonicalFieldMapper


class FieldMappingOverrideService:
    """Persist per-dataset mapping overrides without changing stored files."""

    def __init__(self, mapper: CanonicalFieldMapper | None = None) -> None:
        self._mapper = mapper or CanonicalFieldMapper()

    def get_overrides(self, db: Session, dataset_id: int) -> dict[str, str]:
        rows = db.scalars(
            select(DatasetFieldMappingOverride)
            .where(DatasetFieldMappingOverride.dataset_id == dataset_id)
            .order_by(DatasetFieldMappingOverride.source_column)
        ).all()
        return {row.source_column: row.target_field for row in rows}

    def replace_overrides(
        self,
        db: Session,
        dataset: Dataset,
        overrides: dict[str, str],
    ) -> dict[str, str]:
        """Validate then atomically replace one dataset's complete override set."""
        try:
            frame = self._load_latest_cleaned_frame(db, dataset)
            self._mapper.validate_overrides(frame, overrides)
            db.execute(
                delete(DatasetFieldMappingOverride).where(
                    DatasetFieldMappingOverride.dataset_id == dataset.id
                )
            )
            db.add_all(
                DatasetFieldMappingOverride(
                    dataset_id=dataset.id,
                    source_column=source,
                    target_field=target,
                )
                for source, target in overrides.items()
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        return dict(overrides)

    def get_runtime_mapping(self, db: Session, dataset: Dataset) -> dict[str, object]:
        frame = self._load_latest_cleaned_frame(db, dataset)
        overrides = self.get_overrides(db, dataset.id)
        _mapped_frame, field_mapping = self._mapper.map_dataframe(frame, overrides=overrides)
        return {"overrides": overrides, "field_mapping": field_mapping}

    @staticmethod
    def _load_latest_cleaned_frame(db: Session, dataset: Dataset) -> pd.DataFrame:
        run = db.scalar(
            select(DatasetCleaningRun)
            .where(DatasetCleaningRun.dataset_id == dataset.id)
            .order_by(DatasetCleaningRun.id.desc())
            .limit(1)
        )
        if run is None:
            raise ValueError("请先完成数据清洗，再配置字段映射")
        path = get_settings().resolved_storage_root / Path(run.cleaned_storage_path)
        if not path.is_file():
            raise ValueError("清洗后的数据文件不存在，请重新清洗")
        return pd.read_csv(path, encoding="utf-8-sig")
