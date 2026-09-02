"""Tests for the privacy boundary of structured audit events."""

import logging

import pytest

from cheq_churn_mcp.observability.audit import AuditLogger


def test_audit_event_records_control_shape_without_pii(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("test.audit")
    audit = AuditLogger(logger)

    with caplog.at_level(logging.INFO, logger="test.audit"):
        result = audit.run(
            "get_customer_snapshot",
            {
                "customer_id": "0002-ORFBO",
                "filters": {"churn_reason": "Don't know"},
            },
            lambda: "ok",
        )

    assert result == "ok"
    event = caplog.messages[-1]
    assert '"customer_lookup_requested": true' in event
    assert '"filter_fields": ["churn_reason"]' in event
    assert "0002-ORFBO" not in event
    assert "Don't know" not in event


def test_audit_event_records_errors_without_exception_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("test.audit.error")
    audit = AuditLogger(logger)

    with caplog.at_level(logging.INFO, logger="test.audit.error"):
        with pytest.raises(ValueError, match="private details"):
            audit.run("analyze_customers", {"customer_id": "secret-id"}, _raise_private_error)

    event = caplog.messages[-1]
    assert '"outcome": "error"' in event
    assert "private details" not in event
    assert "secret-id" not in event


def _raise_private_error() -> None:
    raise ValueError("private details")
