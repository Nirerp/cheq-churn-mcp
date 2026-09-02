"""Typed, constrained input schemas for MCP tools."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cheq_churn_mcp.domain.dimensions import DIMENSIONS
from cheq_churn_mcp.domain.metrics import METRICS

MAX_FILTER_VALUE_LENGTH = 100
MAX_FILTER_VALUES = 25
MAX_GROUP_BY_DIMENSIONS = 2
MAX_RESULT_ROWS = 100

FilterValue = Annotated[str, Field(min_length=1, max_length=MAX_FILTER_VALUE_LENGTH)]
FilterValues = Annotated[list[FilterValue], Field(min_length=1, max_length=MAX_FILTER_VALUES)]


class NumericRange(BaseModel):
    """Inclusive range for an allowlisted numeric customer attribute."""

    model_config = ConfigDict(extra="forbid")
    minimum: float | None = None
    maximum: float | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> NumericRange:
        if self.minimum is None and self.maximum is None:
            raise ValueError("at least one numeric range bound is required")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot exceed maximum")
        return self


class CustomerFilters(BaseModel):
    """The complete filter language accepted by the aggregate tool."""

    model_config = ConfigDict(extra="forbid")
    churn: Literal[0, 1] | None = None
    contract: FilterValue | FilterValues | None = None
    internet_type: FilterValue | FilterValues | None = None
    payment_method: FilterValue | FilterValues | None = None
    customer_status: FilterValue | FilterValues | None = None
    churn_category: FilterValue | FilterValues | None = None
    churn_reason: FilterValue | FilterValues | None = None
    reason_intent: Literal["unclear_reason"] | None = None
    age: NumericRange | None = None
    monthly_charge: NumericRange | None = None
    tenure_months: NumericRange | None = None

    @model_validator(mode="after")
    def reject_ambiguous_reason_filters(self) -> CustomerFilters:
        if self.reason_intent is not None and self.churn_reason is not None:
            raise ValueError("reason_intent and churn_reason cannot be combined")
        return self


class AnalyzeCustomersRequest(BaseModel):
    """Input for deterministic aggregate analysis."""

    model_config = ConfigDict(extra="forbid")
    metric: str = Field(default="customer_count")
    group_by: list[str] = Field(default_factory=list, max_length=MAX_GROUP_BY_DIMENSIONS)
    filters: CustomerFilters = Field(default_factory=CustomerFilters)
    limit: int = Field(default=20, ge=1, le=MAX_RESULT_ROWS)

    @model_validator(mode="after")
    def validate_registry_references(self) -> AnalyzeCustomersRequest:
        if self.metric not in METRICS:
            raise ValueError(f"metric must be one of: {', '.join(sorted(METRICS))}")
        unknown_dimensions = sorted(set(self.group_by) - DIMENSIONS.keys())
        if unknown_dimensions:
            raise ValueError(
                "group_by contains unsupported dimensions: " + ", ".join(unknown_dimensions)
            )
        if len(set(self.group_by)) != len(self.group_by):
            raise ValueError("group_by dimensions must not repeat")
        return self


class CustomerSnapshotRequest(BaseModel):
    """Input for a tightly scoped single-customer lookup."""

    model_config = ConfigDict(extra="forbid")
    customer_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9-]+$")
