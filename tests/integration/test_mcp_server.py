"""In-process MCP contract tests using FastMCP's client transport."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client

from cheq_churn_mcp.server import create_server


@pytest.mark.asyncio
async def test_server_exposes_typed_tools_and_returns_structured_content(
    customer_csv: Path,
) -> None:
    async with Client(create_server(customer_csv)) as client:
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
