from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


PredictionType = Literal[
    "equipment_risk",
    "energy_consumption",
    "production_completion",
]
ScopeType = Literal["equipment", "production_line", "factory"]
PredictionRiskLevel = Literal["高风险", "中风险", "正常", "数据不足"]
PredictionAiMode = Literal["deepseek", "rule_based"]


class ManufacturingPredictionSnapshotCreate(BaseModel):
    """Validated immutable input for a manufacturing prediction snapshot."""

    prediction_type: PredictionType
    scope_type: ScopeType
    scope_name: str | None = Field(default=None, min_length=1, max_length=100)
    period_start: date | None = None
    period_end: date | None = None
    forecast_horizon_days: int = Field(ge=1, le=365)
    algorithm_version: str = Field(min_length=1, max_length=50)
    risk_level: PredictionRiskLevel | None = None
    data_snapshot: dict
    prediction_result: dict
    ai_mode: PredictionAiMode
    ai_summary: str = Field(min_length=1)
    generated_at: datetime


class ManufacturingPredictionSnapshotResponse(ManufacturingPredictionSnapshotCreate):
    id: int
    user_id: int
    created_at: datetime


class ManufacturingPredictionCreateRequest(BaseModel):
    """Request for one or more deterministic manufacturing prediction runs."""

    prediction_types: list[PredictionType] = Field(min_length=1)
    equipment_name: str | None = Field(default=None, min_length=1, max_length=100)
    production_line: str | None = Field(default=None, min_length=1, max_length=100)
    forecast_horizon_days: int = Field(default=7, ge=1, le=365)


class ManufacturingPredictionResponse(BaseModel):
    id: int
    prediction_type: PredictionType
    risk_level: PredictionRiskLevel | None
    prediction_result: dict


class ManufacturingPredictionListResponse(BaseModel):
    items: list[ManufacturingPredictionResponse]
    total: int
    page: int
    page_size: int
