from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class DatasetCleaningRun(Base):
    __tablename__ = "dataset_cleaning_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    cleaned_storage_path: Mapped[str] = mapped_column(String(500), unique=True)
    original_row_count: Mapped[int] = mapped_column(Integer)
    cleaned_row_count: Mapped[int] = mapped_column(Integer)
    removed_empty_rows: Mapped[int] = mapped_column(Integer, default=0)
    removed_duplicate_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_value_count: Mapped[int] = mapped_column(Integer, default=0)
    missing_value_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
