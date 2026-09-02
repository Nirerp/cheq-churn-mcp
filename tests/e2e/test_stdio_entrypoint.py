"""Black-box test of the exact stdio command configured for Codex."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports.stdio import StdioTransport

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.asyncio
async def test_console_entrypoint_serves_mcp_tools_over_stdio(customer_csv: Path) -> None:
    transport = StdioTransport(
        command="uv",
        args=["run", "cheq-churn-mcp"],
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "CHEQ_DATASET_PATH": str(customer_csv)},
    )

    async with Client(transport) as client:
        tools = await client.list_tools()
        result = await client.call_tool("describe_dataset")

    assert {tool.name for tool in tools} == {
        "analyze_customers",
        "data_quality_summary",
        "describe_dataset",
    }
    assert result.data["customer_count"] == 2


@pytest.mark.asyncio
async def test_console_entrypoint_exposes_snapshots_only_in_trusted_demo_mode(
    customer_csv: Path,
) -> None:
    transport = StdioTransport(
        command="uv",
        args=["run", "cheq-churn-mcp"],
        cwd=str(PROJECT_ROOT),
        env={
            **os.environ,
            "CHEQ_DATASET_PATH": str(customer_csv),
            "CHEQ_ENABLE_SNAPSHOT_LOOKUPS": "1",
        },
    )

    async with Client(transport) as client:
        tools = await client.list_tools()
        result = await client.call_tool(
            "get_customer_snapshot", {"customer_id": "0001-AAAAA"}
        )

    assert "get_customer_snapshot" in {tool.name for tool in tools}
    assert "customer_id" not in result.data["customer"]
