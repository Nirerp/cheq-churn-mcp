"""Tests for bounded trusted-demo customer identifier discovery."""

from pathlib import Path

from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.schemas.requests import CustomerIdDiscoveryRequest
from cheq_churn_mcp.services.customer_discovery import CustomerDiscoveryService


def test_discovery_is_filtered_bounded_and_deterministic(customer_csv: Path) -> None:
    repository = CustomerRepository(customer_csv)
    repository.open()

    response = CustomerDiscoveryService(repository).find_ids(
        CustomerIdDiscoveryRequest(
            filters={"country": ["Canada", "United States"]},
            purpose="data_quality",
            limit=1,
        )
    )

    assert response.customer_ids == ["0001-AAAAA"]
    assert response.returned_count == 1
    assert response.more_available is True
    repository.close()
