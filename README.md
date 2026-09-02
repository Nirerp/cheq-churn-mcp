# Trustworthy Churn Insights MCP

Local, policy-aware analytics MCP for CHEQ's AI Engineer home assignment.

It serves deterministic aggregate analysis over the Telco Customer Churn dataset
through a local stdio MCP server. The server never accepts arbitrary SQL and
does not include an LLM or vector database: this source is a structured
customer snapshot with controlled churn-reason labels, not a text corpus.

## Included tools

- `describe_dataset` — source provenance, supported fields, and limitations.
- `analyze_customers` — allowlisted aggregate metrics, filters, and dimensions.
- `get_customer_snapshot` — single-customer lookup with a narrow safe projection.
- `data_quality_summary` — uniqueness and core completeness checks.

Every aggregate result includes the pinned Hugging Face dataset revision and
the applied filter definition. Grouped aggregates suppress groups below five
customers.

## Run locally

Do not commit downloaded source data. After confirming source attribution and
redistribution terms, materialize the pinned source into the ignored local cache:

```bash
uv run python scripts/bootstrap_data.py
```

Run the MCP server over stdio:

```bash
uv run cheq-churn-mcp
```

For a different local snapshot, set `CHEQ_DATASET_PATH` to its CSV path. The
server writes protocol messages to stdout; diagnostics go to stderr.

## Verify

```bash
uv sync --all-groups
uv run ruff check .
uv run pytest
```

The assignment PDF, datasets/spreadsheets, and working design documents are
intentionally local-only and excluded by `.gitignore`.
