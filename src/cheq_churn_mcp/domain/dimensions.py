"""Allowlisted dimensions, operators, and filter rules."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DimensionDefinition:
    """A safe grouping or categorical filtering field."""

    column: str
    label: str


DIMENSIONS: dict[str, DimensionDefinition] = {
    "contract": DimensionDefinition("contract", "Contract"),
    "internet_type": DimensionDefinition("internet_type", "Internet type"),
    "payment_method": DimensionDefinition("payment_method", "Payment method"),
    "churn_category": DimensionDefinition("churn_category", "Churn category"),
    "churn_reason": DimensionDefinition("churn_reason", "Churn reason"),
    "customer_status": DimensionDefinition("customer_status", "Customer status"),
    "gender": DimensionDefinition("gender", "Gender"),
    "offer": DimensionDefinition("offer", "Offer"),
}
