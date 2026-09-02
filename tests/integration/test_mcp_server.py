"""In-process MCP contract tests using FastMCP's client transport."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from cheq_churn_mcp.server import create_server


@pytest.mark.asyncio
async def test_server_exposes_typed_tools_and_returns_structured_content(
    customer_csv: Path,
) -> None:
    async with Client(create_server(customer_csv, enable_customer_snapshots=True)) as client:
        tools = await client.list_tools()
        result = await client.call_tool(
            "analyze_customers",
            {"metric": "churned_customers", "filters": {"reason_intent": "unclear_reason"}},
        )

    assert {tool.name for tool in tools} == {
        "analyze_customers",
        "data_quality_summary",
        "describe_dataset",
        "get_customer_snapshot",
    }
    assert result.is_error is False
    assert result.data["rows"] == [{"eligible_customers": 1, "value": 1}]


@pytest.mark.asyncio
async def test_server_defaults_to_aggregate_only_tools(customer_csv: Path) -> None:
    async with Client(create_server(customer_csv)) as client:
        tools = await client.list_tools()
        description = await client.call_tool("describe_dataset")

    assert {tool.name for tool in tools} == {
        "analyze_customers",
        "data_quality_summary",
        "describe_dataset",
    }
    assert "customer_id" not in description.data["supported_analytics"]["filter_fields"]
    assert description.data["supported_analytics"]["limits"] == {
        "max_group_by_dimensions": 2,
        "max_result_rows": 100,
        "max_filter_values_per_field": 25,
        "max_filter_value_length": 100,
    }
    assert "identifier discovery is unsupported" in description.data["identifier_policy"]


@pytest.mark.asyncio
async def test_server_returns_safe_actionable_errors(customer_csv: Path) -> None:
    async with Client(create_server(customer_csv, enable_customer_snapshots=True)) as client:
        with pytest.raises(ToolError, match="INVALID_ARGUMENT"):
            await client.call_tool("analyze_customers", {"metric": "freeform_sql"})
        with pytest.raises(ToolError, match="NOT_FOUND"):
            await client.call_tool("get_customer_snapshot", {"customer_id": "9999-NOTFOUND"})
