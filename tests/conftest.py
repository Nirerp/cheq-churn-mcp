"""Runtime-only test data; no dataset or spreadsheet fixture is tracked in Git."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cheq_churn_mcp.data.contract import COLUMN_ALIASES


@pytest.fixture
def customer_csv(tmp_path: Path) -> Path:
    """Create a small valid source-shaped CSV for repository and service tests."""
    source_columns = list(COLUMN_ALIASES.values())
    rows = [
        {
            "Customer ID": "0001-AAAAA",
            "Age": 30,
            "Churn": 1,
            "Churn Category": "Competitor",
            "Churn Reason": "Don't know",
            "Churn Score": 80,
            "Customer Status": "Churned",
            "Contract": "Month-to-Month",
            "Internet Type": "Fiber Optic",
            "Gender": "Female",
            "Married": 0,
            "Monthly Charge": 95.0,
            "Payment Method": "Bank Withdrawal",
            "Satisfaction Score": 1,
            "Tenure in Months": 3,
            "Total Charges": 285.0,
            "Total Revenue": 285.0,
            "Number of Dependents": 0,
            "Number of Referrals": 0,
            "Avg Monthly GB Download": 50,
            "Offer": "Offer A",
        },
        {
            "Customer ID": "0002-BBBBB",
            "Age": 48,
            "Churn": 0,
            "Churn Category": "",
            "Churn Reason": "",
            "Churn Score": 25,
            "Customer Status": "Stayed",
            "Contract": "Two Year",
            "Internet Type": "DSL",
            "Gender": "Male",
            "Married": 1,
            "Monthly Charge": 60.0,
            "Payment Method": "Credit Card",
            "Satisfaction Score": 4,
            "Tenure in Months": 30,
            "Total Charges": 1800.0,
            "Total Revenue": 1800.0,
            "Number of Dependents": 2,
            "Number of Referrals": 1,
            "Avg Monthly GB Download": 20,
            "Offer": "",
        },
    ]
    path = tmp_path / "customers.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=source_columns)
        writer.writeheader()
        writer.writerows(rows)
    return path
