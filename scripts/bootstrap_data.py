"""Bootstrap the pinned churn dataset into the ignored local data cache."""

from __future__ import annotations

import argparse
from pathlib import Path

from cheq_churn_mcp.data.bootstrap import bootstrap_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PROJECT_ROOT / "data",
        help="Directory for the local dataset cache (default: ./data).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing materialized churn CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = bootstrap_dataset(args.data_dir, overwrite=args.overwrite)
    print(
        f"Materialized {result.row_count:,} rows and {result.column_count} columns "
        f"at {result.dataset_path}"
    )


if __name__ == "__main__":
    main()
