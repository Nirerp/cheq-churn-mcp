"""Smoke tests for the installable package boundary."""

from cheq_churn_mcp.main import main


def test_console_entrypoint_is_callable() -> None:
    """The packaging entrypoint stays importable as the implementation grows."""
    assert callable(main)
