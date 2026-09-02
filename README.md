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

Or use the complete local demo path; it bootstraps the source, runs validation,
then starts the stdio MCP process:

```bash
make demo
```

Run the MCP server over stdio:

```bash
uv run cheq-churn-mcp
```

For a different local snapshot, set `CHEQ_DATASET_PATH` to its CSV path. The
server writes protocol messages to stdout; diagnostics go to stderr.

## Connect an MCP client

First clone the repository and run `uv sync --all-groups`. The data bootstrap
is deliberately local: the dataset is ignored by Git and must be materialized
on each machine before the server starts.

### Codex

Copy the table in [`examples/codex.config.toml`](examples/codex.config.toml)
into `~/.codex/config.toml`, or into `.codex/config.toml` for a trusted clone.
Replace `/ABSOLUTE/PATH/TO/cheq-churn-mcp` with the clone's absolute path, then
restart Codex. Codex supports local stdio servers in `config.toml` through an
`[mcp_servers.<name>]` table.

### Claude Desktop

Merge [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json)
into the Claude Desktop MCP configuration and replace the placeholder absolute
path. Restart Claude Desktop after saving.

## Example business prompts

These are natural-language prompts for the MCP host. The host should select a
tool; it must not generate arbitrary SQL.

- “What percentage of customers churned?” → `analyze_customers(metric="churn_rate")`
- “Which contract has the highest churn rate?” → `analyze_customers` with
  `metric="churn_rate"` and `group_by=["contract"]`
- “How many churned customers said they don't know why?” → `analyze_customers`
  with `metric="churned_customers"` and `filters={"reason_intent": "unclear_reason"}`
- “Show the operational churn snapshot for customer `0002-ORFBO`.” →
  `get_customer_snapshot(customer_id="0002-ORFBO")`

## Verify

```bash
uv sync --all-groups
uv run ruff check .
uv run pytest
```

The assignment PDF, datasets/spreadsheets, and working design documents are
intentionally local-only and excluded by `.gitignore`.
