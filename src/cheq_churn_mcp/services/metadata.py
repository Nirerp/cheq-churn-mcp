"""Dataset metadata and data-quality summary services."""

from cheq_churn_mcp.data.contract import COLUMN_ALIASES, DATASET_ID, DATASET_REVISION
from cheq_churn_mcp.data.repository import CustomerRepository
from cheq_churn_mcp.domain.dimensions import DIMENSIONS
from cheq_churn_mcp.domain.intents import REASON_INTENTS
from cheq_churn_mcp.domain.metrics import METRICS
from cheq_churn_mcp.schemas.requests import (
    MAX_FILTER_VALUE_LENGTH,
    MAX_FILTER_VALUES,
    MAX_GROUP_BY_DIMENSIONS,
    MAX_RESULT_ROWS,
    CustomerFilters,
)


class MetadataService:
    """Expose source facts that help an agent use the tools correctly."""

    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def describe_dataset(self) -> dict[str, object]:
        """Describe the materialized analytic snapshot and its important limitation."""
        row = self._repository.fetch_one("SELECT COUNT(*) AS customer_count FROM customers")
        return {
            "dataset_id": DATASET_ID,
            "dataset_revision": DATASET_REVISION,
            "customer_count": row["customer_count"] if row else 0,
            "source_fields": sorted(COLUMN_ALIASES),
            "supported_analytics": {
                "metrics": {
                    name: {
                        "label": definition.label,
                        "definition": definition.definition,
                        "unit": definition.unit,
                    }
                    for name, definition in METRICS.items()
                },
                "group_by_dimensions": {
                    name: definition.label for name, definition in DIMENSIONS.items()
                },
                "filter_fields": sorted(CustomerFilters.model_fields),
                "reason_intents": {
                    name: intent.definition for name, intent in REASON_INTENTS.items()
                },
                "limits": {
                    "max_group_by_dimensions": MAX_GROUP_BY_DIMENSIONS,
                    "max_result_rows": MAX_RESULT_ROWS,
                    "max_filter_values_per_field": MAX_FILTER_VALUES,
                    "max_filter_value_length": MAX_FILTER_VALUE_LENGTH,
                },
            },
            "identifier_policy": (
                "customer_id is present only in the source schema. It is not an aggregate "
                "filter or grouping and identifier discovery is unsupported."
            ),
            "limitations": [
                "This is a static customer snapshot rather than event-level time series data.",
                "Churn Reason is a controlled categorical label, not a free-text response corpus.",
            ],
        }

    def data_quality_summary(self) -> dict[str, object]:
        """Return compact completeness checks for the fields exposed to tools."""
        row = self._repository.fetch_one(
            """
            SELECT
                COUNT(*) AS customer_count,
                COUNT(DISTINCT customer_id) AS distinct_customer_count,
                COUNT(*) - COUNT(customer_id) AS missing_customer_id_count,
                COUNT(*) - COUNT(churn) AS missing_churn_count,
                COUNT(*) - COUNT(churn_reason) AS missing_churn_reason_count
            FROM customers
            """
        )
        return {
            "dataset_id": DATASET_ID,
            "dataset_revision": DATASET_REVISION,
            "checks": row or {},
            "notes": [
                "Null Churn Reason values are expected for customers who did not churn.",
                "The bootstrap step validates uniqueness of customer_id before serving queries.",
            ],
        }
