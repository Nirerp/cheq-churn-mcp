"""Pinned Hugging Face dataset materialization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DATASET_ID = "aai510-group1/telco-customer-churn"
DATASET_REVISION = "c18fe6295a6ca80ca26627a6627c6f11ccd21d86"
DATASET_SPLITS = ("train", "validation", "test")


@dataclass(frozen=True)
class BootstrapResult:
    """Locations and basic provenance for a materialized analytic snapshot."""

    dataset_path: Path
    metadata_path: Path
    row_count: int
    column_count: int


def bootstrap_dataset(data_dir: Path, *, overwrite: bool = False) -> BootstrapResult:
    """Materialize all source partitions as one local analytic CSV.

    The source data remains outside Git. Callers should verify source licensing
    and attribution requirements before using this download command.
    """
    import pandas as pd
    from datasets import load_dataset

    from cheq_churn_mcp.data.contract import validate_source_columns

    data_dir = data_dir.resolve()
    dataset_path = data_dir / "telco_customer_churn.csv"
    metadata_path = data_dir / "telco_customer_churn.metadata.json"

    if dataset_path.exists() and not overwrite:
        raise FileExistsError(
            f"{dataset_path} already exists. Pass overwrite=True to replace it."
        )

    dataset = load_dataset(DATASET_ID, revision=DATASET_REVISION)
    missing_splits = [split for split in DATASET_SPLITS if split not in dataset]
    if missing_splits:
        raise ValueError(f"Expected source splits are missing: {missing_splits}")

    frames = [dataset[split].to_pandas() for split in DATASET_SPLITS]
    customers = pd.concat(frames, ignore_index=True)

    validate_source_columns(set(customers.columns))
    if not customers["Customer ID"].is_unique:
        raise ValueError("Dataset contract violation: Customer ID values are not unique.")

    data_dir.mkdir(parents=True, exist_ok=True)
    customers.to_csv(dataset_path, index=False)
    metadata_path.write_text(
        json.dumps(
            {
                "dataset_id": DATASET_ID,
                "revision": DATASET_REVISION,
                "splits": list(DATASET_SPLITS),
                "row_count": len(customers),
                "column_count": len(customers.columns),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return BootstrapResult(
        dataset_path=dataset_path,
        metadata_path=metadata_path,
        row_count=len(customers),
        column_count=len(customers.columns),
    )
