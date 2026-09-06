# Trustworthy Churn Insights MCP

Local, policy-aware analytics MCP for CHEQ's AI Engineer home assignment.

It serves deterministic aggregate analysis over the Telco Customer Churn dataset
through a local stdio MCP server. The server never accepts arbitrary SQL and
does not include an LLM or vector database: this source is a structured
customer snapshot with controlled churn-reason labels, not a text corpus.

## Included tools

- `describe_dataset` — source provenance, supported fields, and limitations.
- `analyze_customers` — allowlisted aggregate metrics, filters, and dimensions.
- `data_quality_summary` — uniqueness and core completeness checks.

The default server is aggregate-only. It intentionally does not expose any
customer lookup or ID-discovery tool.

The separately configured trusted-demo server also exposes
`find_customer_ids` and `get_customer_snapshot`. This is an explicit local
capability switch for demonstrating privileged workflows, not authenticated
RBAC.

Every aggregate result includes the pinned Hugging Face dataset revision and
the applied filter definition. Grouped aggregates suppress groups below five
customers and report the count of suppressed groups.

## Error behavior and safety

The server never accepts raw SQL. It compiles only allowlisted metrics,
dimensions, filters, and operators into parameterized DuckDB queries.

- A mistyped metric, unsupported grouping, malformed customer ID, or conflicting
  filter returns an actionable `INVALID_ARGUMENT` tool error.
- In trusted-demo mode, a valid customer lookup with no matching record returns
  `NOT_FOUND`.
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

For a controlled local demonstration of bounded identifier discovery and
known-ID snapshots, use the explicit trusted-demo mode instead:

```bash
make demo-trusted
```

This exposes `find_customer_ids` for a non-empty allowlisted filter, an
allowlisted purpose, and at most 10 results. It also exposes
`get_customer_snapshot`; the caller can request only the safe fields it needs,
including coarse country. It is a local demo switch, not authentication or
RBAC.

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

### Standard aggregate-only mode

This is the normal configuration. It exposes only aggregate tools and cannot
look up or discover customer IDs.

#### Codex with the Makefile

Install the server for the current clone with:

```bash
make install-codex
```

It refuses to overwrite an existing `cheq-churn` configuration. To inspect the
registered server, run `codex mcp get cheq-churn`; restart Codex afterward.
#### Claude Code with the Makefile

With the Claude Code CLI installed, register the same local server with:

```bash
make install-claude-code
```

This uses Claude Code's `claude mcp add` command.

#### Manual Codex configuration

This server is local stdio, not an HTTP service. Add the following to
`~/.codex/config.toml`, or to `.codex/config.toml` in a trusted clone, and
replace the placeholder with the clone's absolute path:

```toml
[mcp_servers.cheq-churn]
command = "uv"
args = ["run", "--directory", "/ABSOLUTE/PATH/TO/cheq-churn-mcp", "cheq-churn-mcp"]
```

Restart Codex after saving. There is no `0.0.0.0:port` address in this local
configuration because Codex starts the process and communicates over stdin and
stdout.

#### Manual Claude Code configuration

Create `.mcp.json` in the clone root, or add this server entry to an existing
`.mcp.json` file:

```json
{
  "mcpServers": {
    "cheq-churn": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/ABSOLUTE/PATH/TO/cheq-churn-mcp",
        "cheq-churn-mcp"
      ]
    }
  }
}
```

Alternatively, run `make print-mcp-config` to generate both ready-to-paste
entries for this clone. Claude Code requires approval before using a
project-scoped server from `.mcp.json`.

When the demo is over, remove only this server entry with:

```bash
make remove-codex
```

For Claude Code, run:

```bash
make remove-claude-code
```

### Trusted local demonstration: bounded ID discovery and lookups

This is not an "admin" mode and not RBAC. A local stdio process has no trusted
caller identity. It is a deliberately separate, opt-in demonstration mode for
bounded identifier discovery and known-ID lookup. The default `cheq-churn`
server remains aggregate-only.

#### Codex or Claude Code with the Makefile

Register a separately named trusted-demo server:

```bash
make install-codex-trusted
# or
make install-claude-code-trusted
```

Restart the client, then ask it to find up to 10 IDs using a non-empty
allowlisted filter and one of these purpose codes: `churn_investigation`,
`customer_support`, `data_quality`, or `security_investigation`. You can then
request selected safe fields for a returned or already-known ID. A valid-looking
ID that is not in the dataset returns `NOT_FOUND`; malformed or unbounded
requests return `INVALID_ARGUMENT`. Remove the server when the demonstration
ends:

```bash
make remove-codex-trusted
# or
make remove-claude-code-trusted
```

#### Manual trusted-demo configuration

The only difference from the standard configuration is the environment
variable `CHEQ_ENABLE_SNAPSHOT_LOOKUPS=1`. For Codex, add a separately named
entry to `config.toml`:

```toml
[mcp_servers.cheq-churn-trusted]
command = "uv"
args = ["run", "--directory", "/ABSOLUTE/PATH/TO/cheq-churn-mcp", "cheq-churn-mcp"]

[mcp_servers.cheq-churn-trusted.env]
CHEQ_ENABLE_SNAPSHOT_LOOKUPS = "1"
```

For Claude Code, add this entry under `mcpServers` in `.mcp.json`:

```json
{
  "cheq-churn-trusted": {
    "type": "stdio",
    "command": "uv",
    "args": [
      "run",
      "--directory",
      "/ABSOLUTE/PATH/TO/cheq-churn-mcp",
      "cheq-churn-mcp"
    ],
    "env": {
      "CHEQ_ENABLE_SNAPSHOT_LOOKUPS": "1"
    }
  }
}
```

Alternatively, run `make print-mcp-config-trusted` for ready-to-paste Codex
TOML and Claude Code JSON. Keep the server name `cheq-churn-trusted` so its
elevated local-demo behavior is visible during testing.

For a standalone terminal process rather than a configured MCP client, run:

```bash
make demo-trusted
```

## Example business prompts

These are natural-language prompts for the MCP host. The host should select a
tool; it must not generate arbitrary SQL.

- “What percentage of customers churned?” → `analyze_customers(metric="churn_rate")`
- “Which contract has the highest churn rate?” → `analyze_customers` with
  `metric="churn_rate"` and `group_by=["contract"]`
- “How many churned customers said they don't know why?” → `analyze_customers`
  with `metric="churned_customers"` and `filters={"reason_intent": "unclear_reason"}`
- “How many non-churned customers live outside the United States?” →
  `analyze_customers` with `metric="customer_count"` and
  `filters={"churn": 0, "exclude_country": "United States"}`
- In trusted-demo mode only: “Show the operational churn snapshot for known
  customer `0002-ORFBO`.” → `get_customer_snapshot(customer_id="0002-ORFBO")`
- In trusted-demo mode only: “Which country is known customer `0002-ORFBO` in?”
  → `get_customer_snapshot(customer_id="0002-ORFBO", fields=["country"])`
- In trusted-demo mode only: “Give me one customer ID for someone who churned
  for an unclear reason.” → `find_customer_ids` with
  `filters={"churn": 1, "reason_intent": "unclear_reason"}`,
  `purpose="churn_investigation"`, and `limit=1`

## Verify

```bash
uv sync --all-groups
uv run ruff check .
uv run pytest
```

The assignment PDF, datasets/spreadsheets, and working design documents are
intentionally local-only and excluded by `.gitignore`.

## Docker

The image deliberately excludes the local dataset. Build it, then mount the
ignored local cache read-only when running the stdio server:

```bash
docker build --tag cheq-churn-mcp:local .
docker run -i --rm -v "$(pwd)/data:/app/data:ro" cheq-churn-mcp:local
```

To use a dataset mounted elsewhere in the container, set
`CHEQ_DATASET_PATH` to its in-container CSV path. The bootstrap stores newly
materialized data and metadata owner-only and writes them atomically. If you
bootstrapped this repository before that protection existed, rerun
`uv run python scripts/bootstrap_data.py --overwrite` once.
