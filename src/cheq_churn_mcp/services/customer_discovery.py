"""Bounded customer-identifier discovery for the explicit trusted demo surface."""

from cheq_churn_mcp.data.contract import CUSTOMER_TABLE, DATASET_ID, DATASET_REVISION
from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.schemas.requests import CustomerIdDiscoveryRequest
from cheq_churn_mcp.schemas.responses import CustomerIdDiscoveryResponse, Provenance
from cheq_churn_mcp.services.analytics import compile_filter_clause


class CustomerDiscoveryService:
    """Find a small deterministic set of identifiers without accepting SQL."""

    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def find_ids(self, request: CustomerIdDiscoveryRequest) -> CustomerIdDiscoveryResponse:
        """Return at most the requested number of matching customer identifiers."""
        where_sql, parameters = compile_filter_clause(request.filters)
        rows = self._repository.fetch_all(
            f"SELECT customer_id FROM {CUSTOMER_TABLE} WHERE {where_sql} "
            "ORDER BY customer_id LIMIT ?",
            [*parameters, request.limit + 1],
        )
        customer_ids = [str(row["customer_id"]) for row in rows[: request.limit]]
        return CustomerIdDiscoveryResponse(
            customer_ids=customer_ids,
            returned_count=len(customer_ids),
            more_available=len(rows) > request.limit,
            provenance=Provenance(
                dataset_id=DATASET_ID,
                dataset_revision=DATASET_REVISION,
                filters_applied=request.filters.model_dump(exclude_none=True),
            ),
        )
