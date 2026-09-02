"""Tests for the local DuckDB snapshot boundary."""

from pathlib import Path

import pytest

from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.errors import DatasetUnavailableError


def test_repository_exposes_canonical_safe_column_names(customer_csv: Path) -> None:
    repository = CustomerRepository(customer_csv)
    repository.open()

    result = repository.fetch_one(
        "SELECT customer_id, churn, monthly_charge FROM customers WHERE customer_id = ?",
        ["0001-AAAAA"],
    )

    assert result == {"customer_id": "0001-AAAAA", "churn": 1, "monthly_charge": 95.0}
    repository.close()


def test_repository_requires_an_existing_local_snapshot(tmp_path: Path) -> None:
    repository = CustomerRepository(tmp_path / "missing.csv")

    with pytest.raises(
        DatasetUnavailableError, match="Run `uv run python scripts/bootstrap_data.py` first"
    ):
        repository.open()
