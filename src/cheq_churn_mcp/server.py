"""FastMCP transport wiring; domain and analytics logic stays outside this module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.domain.policy import CustomerSnapshotField, DiscoveryPurpose
from cheq_churn_mcp.errors import CustomerNotFoundError
from cheq_churn_mcp.observability.audit import AuditLogger
from cheq_churn_mcp.schemas.requests import (
    AnalyzeCustomersRequest,
    CustomerIdDiscoveryRequest,
    CustomerSnapshotRequest,
)
from cheq_churn_mcp.services.analytics import AnalyticsService
from cheq_churn_mcp.services.customer_discovery import CustomerDiscoveryService
from cheq_churn_mcp.services.customer_profile import CustomerProfileService
from cheq_churn_mcp.services.metadata import MetadataService


def create_server(dataset_path: Path, *, enable_customer_snapshots: bool = False) -> FastMCP:
    """Create a local stdio server backed by one validated local dataset snapshot."""
    repository = CustomerRepository(dataset_path)
    repository.open()
    analytics = AnalyticsService(repository)
    discovery = CustomerDiscoveryService(repository)
    profiles = CustomerProfileService(repository)
    metadata = MetadataService(repository, allow_identifier_discovery=enable_customer_snapshots)
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
        def find_customer_ids(
            filters: dict[str, Any],
            purpose: DiscoveryPurpose,
            limit: int = 1,
        ) -> dict[str, Any]:
            """Find up to 10 IDs by safe filters in trusted demo mode; purpose is required."""
            arguments = {"filters": filters, "purpose": purpose, "limit": limit}

            def operation() -> dict[str, Any]:
                try:
                    request = CustomerIdDiscoveryRequest(**arguments)
                except ValidationError as error:
                    raise ToolError(_identifier_discovery_validation_message(error)) from error
                return discovery.find_ids(request).model_dump(mode="json")

            return audit.run("find_customer_ids", arguments, operation)

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


def _identifier_discovery_validation_message(error: ValidationError) -> str:
    """Return useful discovery guidance without echoing sensitive input values."""
    message = error.errors(include_input=False)[0]["msg"]
    return (
        f"INVALID_ARGUMENT: {message}. Identifier discovery requires a stated purpose, one or "
        "more allowlisted filters, and a limit from 1 to 10."
    )
