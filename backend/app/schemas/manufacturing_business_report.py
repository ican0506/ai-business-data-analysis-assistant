from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ManufacturingBusinessReportSnapshotCreate(BaseModel):
    """Validated data that is persisted as an immutable report snapshot."""

    title: str = Field(min_length=1, max_length=200)
    period_start: date | None = None
    period_end: date | None = None
    risk_level: Literal["高风险", "中风险", "正常"]
    ai_mode: Literal["deepseek", "rule_based"]
    summary: str = Field(min_length=1)
    snapshot: dict
    generated_at: datetime


class ManufacturingBusinessReportGenerateRequest(BaseModel):
    """Optional presentation metadata for a newly generated report snapshot."""

    title: str = Field(default="制造业生产经营分析报告", min_length=1, max_length=200)
    period_start: date | None = None
    period_end: date | None = None
