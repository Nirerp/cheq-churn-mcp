"""Tests for safe startup failures before the MCP transport begins."""

import logging

import pytest

from cheq_churn_mcp import main as main_module
from cheq_churn_mcp.errors import DatasetContractError, DatasetUnavailableError


@pytest.mark.parametrize(
    ("error", "expected_log"),
    [
        (
            DatasetUnavailableError("internal path must not reach the user"),
            "Dataset unavailable. Run `uv run python scripts/bootstrap_data.py` before starting.",
        ),
        (
            DatasetContractError("internal schema detail must not reach the user"),
            "Dataset validation failed. Re-bootstrap the pinned source before starting.",
        ),
    ],
)
def test_startup_failures_return_safe_remediation(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
    expected_log: str,
) -> None:
    def fail_startup(*_args: object, **_kwargs: object) -> None:
        raise error

    monkeypatch.setattr(main_module, "create_server", fail_startup)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(SystemExit, match="2"):
            main_module.main()

    assert expected_log in caplog.messages
    assert str(error) not in caplog.text
