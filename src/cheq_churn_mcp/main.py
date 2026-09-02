"""Console entry point for the local stdio MCP server."""

import os
from pathlib import Path

from cheq_churn_mcp.observability.logging import configure_stdio_logging
from cheq_churn_mcp.server import create_server


def main() -> None:
    """Start FastMCP over stdio; protocol output must remain on stdout only."""
    configure_stdio_logging()
    dataset_path = Path(
        os.environ.get("CHEQ_DATASET_PATH", Path.cwd() / "data" / "telco_customer_churn.csv")
    )
    create_server(dataset_path).run()


if __name__ == "__main__":
    main()
