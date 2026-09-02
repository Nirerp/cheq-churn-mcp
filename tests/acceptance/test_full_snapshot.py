"""MCP acceptance tests against the ignored, pinned 7,043-customer source snapshot."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from cheq_churn_mcp.server import create_server


def _server(snapshot_path: Path):
    return create_server(snapshot_path)


@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_describe_dataset_reports_the_full_snapshot_size(full_snapshot_path: Path) -> None:
    async with Client(_server(full_snapshot_path)) as client:
        result = await client.call_tool("describe_dataset")

    assert result.data["customer_count"] == 7043
    assert result.data["dataset_revision"] == "c18fe6295a6ca80ca26627a6627c6f11ccd21d86"


@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_churn_rate_matches_the_pinned_snapshot(full_snapshot_path: Path) -> None:
    async with Client(_server(full_snapshot_path)) as client:
        result = await client.call_tool("analyze_customers", {"metric": "churn_rate"})

    assert result.data["rows"] == [
        {
            "eligible_customers": 7043,
            "value": pytest.approx(26.536987079369588),
        }
    ]


@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_churn_rate_grouped_by_contract_matches_known_results(
    full_snapshot_path: Path,
) -> None:
    async with Client(_server(full_snapshot_path)) as client:
        result = await client.call_tool(
            "analyze_customers", {"metric": "churn_rate", "group_by": ["contract"]}
        )

    assert result.data["rows"] == [
        {
            "contract": "Month-to-Month",
            "eligible_customers": 3610,
            "value": pytest.approx(45.84487534626039),
        },
        {
            "contract": "One Year",
            "eligible_customers": 1550,
            "value": pytest.approx(10.70967741935484),
        },
        {
            "contract": "Two Year",
            "eligible_customers": 1883,
            "value": pytest.approx(2.5491237387148167),
        },
    ]


@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_unclear_reason_intent_matches_the_source_label(full_snapshot_path: Path) -> None:
    async with Client(_server(full_snapshot_path)) as client:
        result = await client.call_tool(
            "analyze_customers",
            {
                "metric": "churned_customers",
                "filters": {"reason_intent": "unclear_reason"},
            },
        )

    assert result.data["rows"] == [{"eligible_customers": 130, "value": 130}]


@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_snapshot_is_limited_to_the_safe_field_projection(full_snapshot_path: Path) -> None:
    async with Client(_server(full_snapshot_path)) as client:
        result = await client.call_tool(
            "get_customer_snapshot", {"customer_id": "0002-ORFBO"}
        )

    customer = result.data["customer"]
    assert customer["customer_id"] == "0002-ORFBO"
    assert "payment_method" not in customer
    assert "age" not in customer
    assert "zip_code" not in customer


@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_unsupported_or_conflicting_requests_are_rejected(full_snapshot_path: Path) -> None:
    async with Client(_server(full_snapshot_path)) as client:
        with pytest.raises(ToolError, match="INVALID_ARGUMENT"):
            await client.call_tool("analyze_customers", {"metric": "raw_sql"})
        with pytest.raises(ToolError, match="INVALID_ARGUMENT"):
            await client.call_tool(
                "analyze_customers",
                {
                    "filters": {
                        "reason_intent": "unclear_reason",
                        "churn_reason": "Don't know",
                    }
                },
            )
