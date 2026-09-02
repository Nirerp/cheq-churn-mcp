"""Compile constrained analytics requests to server-authored DuckDB SQL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cheq_churn_mcp.data.contract import CUSTOMER_TABLE, DATASET_ID, DATASET_REVISION
from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.domain.dimensions import DIMENSIONS
from cheq_churn_mcp.domain.intents import REASON_INTENTS
from cheq_churn_mcp.domain.metrics import METRICS
from cheq_churn_mcp.domain.policy import MINIMUM_AGGREGATE_GROUP_SIZE
from cheq_churn_mcp.schemas.requests import AnalyzeCustomersRequest, CustomerFilters, NumericRange
from cheq_churn_mcp.schemas.responses import AnalyticsResponse, Provenance


@dataclass(frozen=True)
class CompiledAnalyticsQuery:
    """Auditable query plan: SQL text is system-owned and values are bound."""

    sql: str
    parameters: tuple[Any, ...]
    suppression_sql: str | None = None
    suppression_parameters: tuple[Any, ...] = ()


def _where_clause(filters: CustomerFilters) -> tuple[str, list[Any]]:
    fragments: list[str] = []
    parameters: list[Any] = []
    values = filters.model_dump(exclude_none=True)
    for name in (
        "churn", "contract", "internet_type", "payment_method", "customer_status",
        "churn_category", "churn_reason",
    ):
        value = values.get(name)
        if value is None:
            continue
        if isinstance(value, list):
            fragments.append(f"{name} IN ({', '.join('?' for _ in value)})")
            parameters.extend(value)
        else:
            fragments.append(f"{name} = ?")
            parameters.append(value)
    if filters.reason_intent:
        intent = REASON_INTENTS[filters.reason_intent]
        fragments.append(f"churn_reason IN ({', '.join('?' for _ in intent.values)})")
        parameters.extend(intent.values)
    for name in ("age", "monthly_charge", "tenure_months"):
        value = getattr(filters, name)
        if value is not None:
            _append_range(fragments, parameters, name, value)
    return (" AND ".join(fragments) if fragments else "TRUE"), parameters


def _append_range(
    fragments: list[str], parameters: list[Any], column: str, numeric_range: NumericRange
) -> None:
    if numeric_range.minimum is not None:
        fragments.append(f"{column} >= ?")
        parameters.append(numeric_range.minimum)
    if numeric_range.maximum is not None:
        fragments.append(f"{column} <= ?")
        parameters.append(numeric_range.maximum)


def compile_analytics_query(request: AnalyzeCustomersRequest) -> CompiledAnalyticsQuery:
    """Compile an allowlisted request without accepting client-provided SQL."""
    metric = METRICS[request.metric]
    where_sql, parameters = _where_clause(request.filters)
    group_columns = [DIMENSIONS[name].column for name in request.group_by]
    select_parts = [
        *group_columns,
        "COUNT(*) AS eligible_customers",
        f"{metric.expression} AS value",
    ]
    sql = f"SELECT {', '.join(select_parts)} FROM {CUSTOMER_TABLE} WHERE {where_sql}"
    suppression_sql: str | None = None
    suppression_parameters: tuple[Any, ...] = ()
    if group_columns:
        group_sql = ", ".join(group_columns)
        sql += f" GROUP BY {group_sql} HAVING COUNT(*) >= ?"
        parameters.append(MINIMUM_AGGREGATE_GROUP_SIZE)
        sql += f" ORDER BY value DESC NULLS LAST, {group_sql} ASC"
        suppression_sql = (
            "SELECT COUNT(*) AS suppressed_group_count FROM ("
            f"SELECT 1 FROM {CUSTOMER_TABLE} WHERE {where_sql} "
            f"GROUP BY {group_sql} HAVING COUNT(*) < ?"
            ") AS suppressed_groups"
        )
        suppression_parameters = tuple([*parameters[:-1], MINIMUM_AGGREGATE_GROUP_SIZE])
    sql += " LIMIT ?"
    parameters.append(request.limit)
    return CompiledAnalyticsQuery(
        sql=sql,
        parameters=tuple(parameters),
        suppression_sql=suppression_sql,
        suppression_parameters=suppression_parameters,
    )


class AnalyticsService:
    """Execute aggregate analysis and attach concise interpretation metadata."""

    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def analyze(self, request: AnalyzeCustomersRequest) -> AnalyticsResponse:
        """Run an allowlisted aggregation over the locally materialized snapshot."""
        compiled = compile_analytics_query(request)
        rows = self._repository.fetch_all(compiled.sql, compiled.parameters)
        suppressed_group_count = 0
        if compiled.suppression_sql is not None:
            suppression = self._repository.fetch_one(
                compiled.suppression_sql, compiled.suppression_parameters
            )
            suppressed_group_count = int(suppression["suppressed_group_count"])
        return AnalyticsResponse(
            rows=rows,
            provenance=Provenance(
                dataset_id=DATASET_ID,
                dataset_revision=DATASET_REVISION,
                metric_definition=METRICS[request.metric].definition,
                filters_applied=request.filters.model_dump(exclude_none=True),
            ),
            suppressed_group_count=suppressed_group_count,
        )
