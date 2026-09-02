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
customers and report the count of suppressed groups.

## Error behavior and safety

The server never accepts raw SQL. It compiles only allowlisted metrics,
dimensions, filters, and operators into parameterized DuckDB queries.

- A mistyped metric, unsupported grouping, malformed customer ID, or conflicting
  filter returns an actionable `INVALID_ARGUMENT` tool error.
- A valid customer lookup with no matching record returns `NOT_FOUND`.
- An empty aggregate result is valid data, returned as an empty `rows` list.
- Unexpected server failures are masked from the MCP client; they are recorded
  as privacy-safe audit events without customer IDs, filter values, or raw
  exception details.
- If the local snapshot is missing or violates its contract, the server does
  not start and prints a safe remediation command to stderr.

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

Install the server for the current clone with:

```bash
make install-codex
```

It refuses to overwrite an existing `cheq-churn` configuration. To inspect the
registered server, run `codex mcp get cheq-churn`; restart Codex afterward.
Alternatively, `make print-mcp-config` prints a ready-to-paste table with this
clone's absolute path. Codex supports local stdio servers in `config.toml`
through an `[mcp_servers.<name>]` table.

When the demo is over, remove only this server entry with:

```bash
make remove-codex
```

### Claude Code

With the Claude Code CLI installed, register the same local server with:

```bash
make install-claude-code
```

This uses Claude Code's `claude mcp add` command. `make print-mcp-config` also
prints a JSON entry that can be adapted for other MCP clients.

Remove the same server later with:

```bash
make remove-claude-code
```

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
