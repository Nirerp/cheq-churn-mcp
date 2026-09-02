"""Stable JSON-shaped response schemas returned by MCP tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Provenance(BaseModel):
    """Enough context to reproduce and correctly interpret a result."""

    model_config = ConfigDict(extra="forbid")
    dataset_id: str
    dataset_revision: str
    metric_definition: str | None = None
    filters_applied: dict[str, Any] = Field(default_factory=dict)


class AnalyticsResponse(BaseModel):
    """Aggregate results with denominator and suppression context."""

    model_config = ConfigDict(extra="forbid")
    rows: list[dict[str, Any]]
    provenance: Provenance
    suppressed_group_count: int = 0


class CustomerSnapshotResponse(BaseModel):
    """Safe single-customer response; fields are controlled by server policy."""

    model_config = ConfigDict(extra="forbid")
    customer: dict[str, Any] | None
    provenance: Provenance
