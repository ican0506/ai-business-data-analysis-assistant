from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class DatasetFieldMappingOverride(Base):
    __tablename__ = "dataset_field_mapping_overrides"
    __table_args__ = (
        UniqueConstraint("dataset_id", "source_column", name="uk_dataset_mapping_override_source"),
        UniqueConstraint("dataset_id", "target_field", name="uk_dataset_mapping_override_target"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    source_column: Mapped[str] = mapped_column(String(255))
    target_field: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
