"""Tests for safe single-customer projections."""

from pathlib import Path

from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.schemas.requests import CustomerSnapshotRequest
from cheq_churn_mcp.services.customer_profile import CustomerProfileService


def test_snapshot_omits_precise_location_and_payment_data(customer_csv: Path) -> None:
    repository = CustomerRepository(customer_csv)
    repository.open()

    response = CustomerProfileService(repository).get_snapshot(
        CustomerSnapshotRequest(customer_id="0001-AAAAA")
    )

    assert response.customer is not None
    assert "customer_id" not in response.customer
    assert "payment_method" not in response.customer
    assert "age" not in response.customer
    repository.close()
