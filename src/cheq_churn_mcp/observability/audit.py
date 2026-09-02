"""Structured audit-event construction without raw PII."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from time import perf_counter
from typing import Any, TypeVar

T = TypeVar("T")


class AuditLogger:
    """Emit tool-use telemetry without recording customer or filter values."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("cheq_churn_mcp.audit")

    def run(self, tool_name: str, arguments: Mapping[str, Any], operation: Callable[[], T]) -> T:
        """Run an operation and write a privacy-safe success or error event."""
        started_at = perf_counter()
        try:
            result = operation()
        except Exception:
            self._write(tool_name, arguments, "error", started_at)
            raise
        self._write(tool_name, arguments, "success", started_at)
        return result

    def _write(
        self, tool_name: str, arguments: Mapping[str, Any], outcome: str, started_at: float
    ) -> None:
        event = {
            "event": "mcp_tool_call",
            "tool_name": tool_name,
            "outcome": outcome,
            "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            "request_shape": _safe_request_shape(arguments),
        }
        self._logger.info("%s", json.dumps(event, sort_keys=True))


def _safe_request_shape(arguments: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize only safe control fields, never identifiers or filter values."""
    summary: dict[str, Any] = {}
    if "metric" in arguments:
        summary["metric"] = arguments["metric"]
    if "group_by" in arguments:
        summary["group_by"] = arguments["group_by"]
    if "filters" in arguments and isinstance(arguments["filters"], Mapping):
        summary["filter_fields"] = sorted(arguments["filters"])
    if "customer_id" in arguments:
        summary["customer_lookup_requested"] = True
    return summary
