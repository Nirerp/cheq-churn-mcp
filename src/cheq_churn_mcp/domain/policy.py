"""Safe local policy and the production seam for ABAC enforcement."""

MINIMUM_AGGREGATE_GROUP_SIZE = 5
TRUSTED_DEMO_SNAPSHOT_ENV_VAR = "CHEQ_ENABLE_SNAPSHOT_LOOKUPS"

# A local stdio MCP server has no trustworthy caller identity. These fields are
# deliberately omitted from the snapshot tool until an authenticated production
# policy layer is supplied.
CUSTOMER_SNAPSHOT_FIELDS = (
    "customer_status", "churn", "churn_category", "churn_reason",
    "contract", "internet_type", "monthly_charge", "satisfaction_score", "tenure_months",
)


def snapshots_enabled(environment_value: str | None) -> bool:
    """Enable individual snapshots only through an explicit local trusted-demo opt-in."""
    return environment_value == "1"
