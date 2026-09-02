"""Single-customer snapshot service with explicit safe-field policy."""

from cheq_churn_mcp.data.contract import CUSTOMER_TABLE, DATASET_ID, DATASET_REVISION
from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.domain.policy import CUSTOMER_SNAPSHOT_FIELDS
from cheq_churn_mcp.errors import CustomerNotFoundError
from cheq_churn_mcp.schemas.requests import CustomerSnapshotRequest
from cheq_churn_mcp.schemas.responses import CustomerSnapshotResponse, Provenance


class CustomerProfileService:
    """Return a deliberately narrow view of one customer record."""

    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def get_snapshot(self, request: CustomerSnapshotRequest) -> CustomerSnapshotResponse:
        """Look up a single identifier without exposing location or payment detail."""
        fields = ", ".join(CUSTOMER_SNAPSHOT_FIELDS)
        customer = self._repository.fetch_one(
            f"SELECT {fields} FROM {CUSTOMER_TABLE} WHERE customer_id = ?", [request.customer_id]
        )
        if customer is None:
            raise CustomerNotFoundError("Customer was not found in the local snapshot.")
        return CustomerSnapshotResponse(
            customer=customer,
            provenance=Provenance(dataset_id=DATASET_ID, dataset_revision=DATASET_REVISION),
        )
