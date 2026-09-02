"""FastMCP transport wiring; domain and analytics logic stays outside this module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.schemas.requests import AnalyzeCustomersRequest, CustomerSnapshotRequest
from cheq_churn_mcp.services.analytics import AnalyticsService
from cheq_churn_mcp.services.customer_profile import CustomerProfileService
from cheq_churn_mcp.services.metadata import MetadataService


def create_server(dataset_path: Path) -> FastMCP:
    """Create a local stdio server backed by one validated local dataset snapshot."""
    repository = CustomerRepository(dataset_path)
    repository.open()
    analytics = AnalyticsService(repository)
    profiles = CustomerProfileService(repository)
    metadata = MetadataService(repository)
    mcp = FastMCP("CHEQ Churn Insights")

    @mcp.tool
    def describe_dataset() -> dict[str, object]:
        """Explain the dataset, supported fields, provenance, and analytic limitations."""
        return metadata.describe_dataset()

    @mcp.tool
    def data_quality_summary() -> dict[str, object]:
        """Return customer-ID uniqueness and completeness checks for core analytic fields."""
        return metadata.data_quality_summary()

    @mcp.tool
    def analyze_customers(
        metric: str = "customer_count",
        group_by: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Calculate a safe aggregate using allowlisted metrics, filters, and dimensions only."""
        request = AnalyzeCustomersRequest(
            metric=metric,
            group_by=group_by or [],
            filters=filters or {},
            limit=limit,
        )
        return analytics.analyze(request).model_dump(mode="json")

    @mcp.tool
    def get_customer_snapshot(customer_id: str) -> dict[str, Any]:
        """Get an allowlisted, single-customer operational snapshot by exact ID."""
        return profiles.get_snapshot(CustomerSnapshotRequest(customer_id=customer_id)).model_dump(
            mode="json"
        )

    return mcp
