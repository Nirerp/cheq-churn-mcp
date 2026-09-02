"""Console entry point for the local stdio MCP server."""

import logging
import os
from pathlib import Path

from cheq_churn_mcp.domain.policy import TRUSTED_DEMO_SNAPSHOT_ENV_VAR, snapshots_enabled
from cheq_churn_mcp.errors import DatasetContractError, DatasetUnavailableError
from cheq_churn_mcp.observability.logging import configure_stdio_logging
from cheq_churn_mcp.server import create_server


def main() -> None:
    """Start FastMCP over stdio; protocol output must remain on stdout only."""
    configure_stdio_logging()
    dataset_path = Path(
        os.environ.get("CHEQ_DATASET_PATH", Path.cwd() / "data" / "telco_customer_churn.csv")
    )
    try:
        create_server(
            dataset_path,
            enable_customer_snapshots=snapshots_enabled(
                os.environ.get(TRUSTED_DEMO_SNAPSHOT_ENV_VAR)
            ),
        ).run()
    except DatasetUnavailableError:
        logging.getLogger(__name__).error(
            "Dataset unavailable. Run `uv run python scripts/bootstrap_data.py` before starting."
        )
        raise SystemExit(2) from None
    except DatasetContractError:
        logging.getLogger(__name__).error(
            "Dataset validation failed. Re-bootstrap the pinned source before starting."
        )
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
