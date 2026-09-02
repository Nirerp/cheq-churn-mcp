"""Tests for the explicit local trusted-demo opt-in."""

import pytest

from cheq_churn_mcp.domain.policy import snapshots_enabled


@pytest.mark.parametrize(
    ("environment_value", "expected"),
    [(None, False), ("", False), ("true", False), ("0", False), ("1", True)],
)
def test_snapshots_require_the_exact_trusted_demo_opt_in(
    environment_value: str | None,
    expected: bool,
) -> None:
    assert snapshots_enabled(environment_value) is expected
