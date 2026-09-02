"""Metric registry, formulas, null semantics, and display definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDefinition:
    """A server-owned metric expression and the words needed to interpret it."""

    expression: str
    label: str
    definition: str
    unit: str


METRICS: dict[str, MetricDefinition] = {
    "customer_count": MetricDefinition(
        "COUNT(*)", "Customers", "Number of customers matching the supplied filters.", "customers"
    ),
    "churned_customers": MetricDefinition(
        "COUNT(*) FILTER (WHERE churn = 1)",
        "Churned customers",
        "Number of matching customers with Churn equal to 1.",
        "customers",
    ),
    "churn_rate": MetricDefinition(
        "100.0 * AVG(churn)",
        "Churn rate",
        "Percentage of matching customers with Churn equal to 1.",
        "percent",
    ),
    "average_monthly_charge": MetricDefinition(
        "AVG(monthly_charge)",
        "Average monthly charge",
        "Mean Monthly Charge for matching customers; null values are excluded.",
        "currency",
    ),
    "average_tenure_months": MetricDefinition(
        "AVG(tenure_months)",
        "Average tenure",
        "Mean Tenure in Months for matching customers; null values are excluded.",
        "months",
    ),
}
