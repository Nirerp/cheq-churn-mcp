"""FastMCP transport wiring; domain and analytics logic stays outside this module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.domain.policy import CustomerSnapshotField
from cheq_churn_mcp.errors import CustomerNotFoundError
from cheq_churn_mcp.observability.audit import AuditLogger
from cheq_churn_mcp.schemas.requests import AnalyzeCustomersRequest, CustomerSnapshotRequest
from cheq_churn_mcp.services.analytics import AnalyticsService
from cheq_churn_mcp.services.customer_profile import CustomerProfileService
from cheq_churn_mcp.services.metadata import MetadataService


def create_server(dataset_path: Path, *, enable_customer_snapshots: bool = False) -> FastMCP:
    """Create a local stdio server backed by one validated local dataset snapshot."""
    repository = CustomerRepository(dataset_path)
    repository.open()
    analytics = AnalyticsService(repository)
    profiles = CustomerProfileService(repository)
    metadata = MetadataService(repository)
    audit = AuditLogger()
    mcp = FastMCP(
        "CHEQ Churn Insights",
        instructions=(
            "Use these tools for business questions about the locally materialized Telco Customer "
            "Churn snapshot. Do not generate or submit SQL."
        ),
        mask_error_details=True,
    )

    @mcp.tool
    def describe_dataset() -> dict[str, object]:
        """Explain the dataset, supported fields, provenance, and analytic limitations."""
        return audit.run("describe_dataset", {}, metadata.describe_dataset)

    @mcp.tool
    def data_quality_summary() -> dict[str, object]:
        """Return customer-ID uniqueness and completeness checks for core analytic fields."""
        return audit.run("data_quality_summary", {}, metadata.data_quality_summary)

    @mcp.tool
    def analyze_customers(
        metric: str = "customer_count",
        group_by: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Calculate a safe aggregate using allowlisted metrics, filters, and dimensions only."""
        arguments = {
            "metric": metric,
            "group_by": group_by or [],
            "filters": filters or {},
            "limit": limit,
        }

        def operation() -> dict[str, Any]:
            try:
                request = AnalyzeCustomersRequest(**arguments)
            except ValidationError as error:
                raise ToolError(_analytics_validation_message(error)) from error
            return analytics.analyze(request).model_dump(mode="json")

        return audit.run("analyze_customers", arguments, operation)

    if enable_customer_snapshots:

        @mcp.tool
        def get_customer_snapshot(
            customer_id: str,
            fields: list[CustomerSnapshotField] | None = None,
        ) -> dict[str, Any]:
            """Get selected safe fields for an already-known customer ID."""

            def operation() -> dict[str, Any]:
                try:
                    arguments: dict[str, Any] = {"customer_id": customer_id}
                    if fields is not None:
                        arguments["fields"] = fields
                    request = CustomerSnapshotRequest(**arguments)
                except ValidationError as error:
                    raise ToolError(
                        "INVALID_ARGUMENT: use a valid customer_id and one or more allowlisted "
                        "snapshot fields."
                    ) from error
                return profiles.get_snapshot(request).model_dump(mode="json")

            try:
                return audit.run(
                    "get_customer_snapshot",
                    {"customer_id": customer_id, "fields": fields or []},
                    operation,
                )
            except CustomerNotFoundError as error:
                raise ToolError(
                    "NOT_FOUND: no matching customer exists in the local snapshot."
                ) from error

    return mcp


def _analytics_validation_message(error: ValidationError) -> str:
    """Return an agent-actionable validation message without echoing untrusted values."""
    message = error.errors(include_input=False)[0]["msg"]
    return (
        f"INVALID_ARGUMENT: {message}. Use describe_dataset to inspect supported fields and "
        "analyze_customers for allowlisted metrics, filters, and groupings."
    )
