"""Behavioral tests for safe aggregate compilation and execution."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.schemas.requests import AnalyzeCustomersRequest
from cheq_churn_mcp.services.analytics import AnalyticsService, compile_analytics_query


def test_compiler_binds_untrusted_filter_values() -> None:
    request = AnalyzeCustomersRequest(
        filters={"contract": "Month-to-Month' OR 1=1 --"}
    )

    compiled = compile_analytics_query(request)

    assert "Month-to-Month' OR 1=1 --" not in compiled.sql
    assert compiled.parameters == ("Month-to-Month' OR 1=1 --", 20)


def test_unclear_reason_intent_is_counted_as_an_aggregate(customer_csv: Path) -> None:
    repository = CustomerRepository(customer_csv)
    repository.open()
    service = AnalyticsService(repository)

    response = service.analyze(
        AnalyzeCustomersRequest(
            metric="churned_customers",
            filters={"reason_intent": "unclear_reason"},
        )
    )

    assert response.rows == [{"eligible_customers": 1, "value": 1}]
    assert response.provenance.filters_applied == {"reason_intent": "unclear_reason"}
    repository.close()


def test_reason_intent_and_exact_reason_are_mutually_exclusive() -> None:
    with pytest.raises(ValidationError, match="cannot be combined"):
        AnalyzeCustomersRequest(
            filters={"reason_intent": "unclear_reason", "churn_reason": "Don't know"}
        )


def test_grouped_results_report_small_groups_that_were_withheld(customer_csv: Path) -> None:
    repository = CustomerRepository(customer_csv)
    repository.open()

    response = AnalyticsService(repository).analyze(
        AnalyzeCustomersRequest(metric="customer_count", group_by=["contract"])
    )

    assert response.rows == []
    assert response.suppressed_group_count == 2
    repository.close()


def test_filter_values_are_bounded_to_limit_resource_use() -> None:
    with pytest.raises(ValidationError, match="at most 25 items"):
        AnalyzeCustomersRequest(filters={"contract": ["Month-to-Month"] * 26})
    with pytest.raises(ValidationError, match="at most 100 characters"):
        AnalyzeCustomersRequest(filters={"contract": "x" * 101})
