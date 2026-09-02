"""Source schema and data-invariant validation."""

from __future__ import annotations

from collections.abc import Mapping

from cheq_churn_mcp.errors import DatasetContractError

DATASET_ID = "aai510-group1/telco-customer-churn"
DATASET_REVISION = "c18fe6295a6ca80ca26627a6627c6f11ccd21d86"
CUSTOMER_TABLE = "customers"

# The source CSV uses human-readable headers. The application exposes only these
# stable, SQL-safe aliases to compilers and services.
COLUMN_ALIASES: Mapping[str, str] = {
    "customer_id": "Customer ID",
    "age": "Age",
    "churn": "Churn",
    "churn_category": "Churn Category",
    "churn_reason": "Churn Reason",
    "churn_score": "Churn Score",
    "customer_status": "Customer Status",
    "contract": "Contract",
    "internet_type": "Internet Type",
    "gender": "Gender",
    "married": "Married",
    "monthly_charge": "Monthly Charge",
    "payment_method": "Payment Method",
    "satisfaction_score": "Satisfaction Score",
    "tenure_months": "Tenure in Months",
    "total_charges": "Total Charges",
    "total_revenue": "Total Revenue",
    "number_of_dependents": "Number of Dependents",
    "number_of_referrals": "Number of Referrals",
    "avg_monthly_gb_download": "Avg Monthly GB Download",
    "offer": "Offer",
}

REQUIRED_SOURCE_COLUMNS = frozenset(COLUMN_ALIASES.values())


def validate_source_columns(columns: set[str]) -> None:
    """Raise a stable error if a snapshot cannot support documented tools."""
    missing = sorted(REQUIRED_SOURCE_COLUMNS - columns)
    if missing:
        raise DatasetContractError(
            "Dataset contract violation: required columns are missing: " + ", ".join(missing)
        )


def customer_view_select_list() -> str:
    """Return the fixed projection used to create the canonical customer view."""
    return ", ".join(
        f'"{source_name}" AS {canonical_name}'
        for canonical_name, source_name in COLUMN_ALIASES.items()
    )
