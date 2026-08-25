from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class ManufacturingPredictionRun(Base):
    """Immutable snapshot of one deterministic manufacturing prediction run."""

    __tablename__ = "manufacturing_prediction_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prediction_type: Mapped[str] = mapped_column(String(50), index=True)
    scope_type: Mapped[str] = mapped_column(String(50), index=True)
    scope_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    forecast_horizon_days: Mapped[int] = mapped_column(Integer)
    algorithm_version: Mapped[str] = mapped_column(String(50))
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_snapshot: Mapped[dict] = mapped_column(JSON)
    prediction_result: Mapped[dict] = mapped_column(JSON)
    ai_mode: Mapped[str] = mapped_column(String(30))
    ai_summary: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
