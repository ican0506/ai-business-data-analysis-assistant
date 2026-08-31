"""Strict, executable-safe query contracts for the Data Chat feature."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataChatMetric(str, Enum):
    SALES_AMOUNT = "sales_amount"
    SALES_QUANTITY = "sales_quantity"
    ORDER_COUNT = "order_count"
    AVERAGE_ORDER_VALUE = "average_order_value"


class DataChatGroupBy(str, Enum):
    PRODUCT = "product"
    CATEGORY = "category"
    REGION = "region"
    MONTH = "month"


class DataChatSortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class DataChatDateRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: date
    end: date

    @model_validator(mode="after")
    def validate_range(self) -> "DataChatDateRange":
        if self.start > self.end:
            raise ValueError("date_range.start 不能晚于 date_range.end")
        return self


class DataChatFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str | None = Field(default=None, min_length=1, max_length=100)
    product: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=100)


class DataChatSort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: DataChatMetric
    direction: DataChatSortDirection = DataChatSortDirection.DESC


class DataChatQueryPlan(BaseModel):
    """A whitelist-only plan that the MetricQueryEngine can execute safely."""

    model_config = ConfigDict(extra="forbid")

    domain: Literal["order"] = "order"
    metrics: list[DataChatMetric] = Field(min_length=1, max_length=4)
    date_range: DataChatDateRange | None = None
    filters: DataChatFilters = Field(default_factory=DataChatFilters)
    group_by: list[DataChatGroupBy] = Field(default_factory=list, max_length=1)
    sort: DataChatSort | None = None
    limit: int | None = Field(default=None, ge=1, le=100)

    @model_validator(mode="after")
    def validate_grouping(self) -> "DataChatQueryPlan":
        if self.sort is not None and self.sort.metric not in self.metrics:
            raise ValueError("sort.metric 必须包含在 metrics 中")
        if self.group_by and DataChatMetric.AVERAGE_ORDER_VALUE in self.metrics:
            raise ValueError("average_order_value 暂不支持按维度分组")
        return self
