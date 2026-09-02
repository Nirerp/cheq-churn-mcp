"""Read-only DuckDB repository lifecycle and query execution."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb

from cheq_churn_mcp.data.contract import (
    CUSTOMER_TABLE,
    customer_view_select_list,
    validate_source_columns,
)
from cheq_churn_mcp.errors import DatasetContractError, DatasetUnavailableError


class CustomerRepository:
    """Owns an in-memory DuckDB connection over one local, immutable CSV snapshot."""

    def __init__(self, dataset_path: Path) -> None:
        self._dataset_path = dataset_path
        self._connection: duckdb.DuckDBPyConnection | None = None

    def open(self) -> None:
        """Load and validate the local CSV once, exposing a canonical customer view."""
        if self._connection is not None:
            return
        if not self._dataset_path.is_file():
            raise DatasetUnavailableError(
                f"Local dataset not found at {self._dataset_path}. "
                "Run `uv run python scripts/bootstrap_data.py` first."
            )

        connection = duckdb.connect(database=":memory:")
        try:
            connection.execute(
                "CREATE TABLE raw_customers AS SELECT * FROM read_csv_auto(?, header = true)",
                [str(self._dataset_path)],
            )
            source_schema = connection.execute("PRAGMA table_info('raw_customers')").fetchall()
            columns = {row[1] for row in source_schema}
            validate_source_columns(columns)
            connection.execute(
                f"CREATE VIEW {CUSTOMER_TABLE} AS "
                f"SELECT {customer_view_select_list()} FROM raw_customers"
            )
            duplicate_ids = connection.execute(
                f"SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM {CUSTOMER_TABLE}"
            ).fetchone()
            if duplicate_ids is None or duplicate_ids[0] != 0:
                raise DatasetContractError(
                    "Dataset contract violation: customer_id values must be unique."
                )
        except Exception:
            connection.close()
            raise
        self._connection = connection

    def fetch_all(self, sql: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        """Execute server-authored, parameterized SQL and return JSON-ready records."""
        connection = self._require_connection()
        cursor = connection.execute(sql, parameters)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def fetch_one(self, sql: str, parameters: Sequence[Any] = ()) -> dict[str, Any] | None:
        """Execute server-authored SQL and return one JSON-ready record, if present."""
        rows = self.fetch_all(sql, parameters)
        return rows[0] if rows else None

    def close(self) -> None:
        """Release the in-memory connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _require_connection(self) -> duckdb.DuckDBPyConnection:
        if self._connection is None:
            raise RuntimeError("CustomerRepository.open() must be called before querying.")
        return self._connection
