"""Application logging configured to stderr for stdio MCP safety."""

import logging
import sys


def configure_stdio_logging() -> None:
    """Keep all diagnostics off stdout, which belongs exclusively to MCP protocol traffic."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
