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

## Quick start

The MCP has two deliberately different access modes. Use the regular server for
normal analytics. Install the trusted-demo server only when you specifically
want to demonstrate customer-ID discovery or known-customer lookup.

### One-time setup

From the cloned repository:

```bash
uv sync --all-groups
make bootstrap
```

`make bootstrap` downloads the pinned 7,043-row dataset into the ignored local
`data/` directory. The dataset is not stored in Git and must be bootstrapped on
each new clone.

### Option A: regular MCP — recommended default

The regular MCP is registered as `cheq-churn`. It exposes only:

- `describe_dataset`
- `analyze_customers`
- `data_quality_summary`

It can answer aggregate questions such as churn counts, rates, reasons, and
grouped comparisons. It cannot discover a customer ID or retrieve an individual
customer snapshot.

Register it with one client:

```bash
# Codex
make install-codex

# Claude Code
make install-claude-code
```

Restart that client after installation. Confirm the registration with
`codex mcp get cheq-churn` or `claude mcp get cheq-churn`, then ask an aggregate
question such as “What percentage of customers churned?”

Remove the regular registration with:

```bash
make remove-codex
# or
make remove-claude-code
```

### Option B: trusted-demo MCP — explicit privileged demo

The trusted-demo MCP is registered separately as `cheq-churn-trusted`. It
exposes all three regular tools plus:

- `find_customer_ids` — returns at most 10 matching IDs; requires a non-empty
  allowlisted filter and an allowlisted purpose code.
- `get_customer_snapshot` — retrieves selected safe fields for an already-known
  or newly discovered ID.

Register it with one client:

```bash
# Codex
make install-codex-trusted

# Claude Code
make install-claude-code-trusted
```

Restart that client after installation. Confirm the registration with
`codex mcp get cheq-churn-trusted` or `claude mcp get cheq-churn-trusted`. You
can then ask: “Using only `cheq-churn-trusted`, give me one customer ID for a
customer who churned for an unclear reason.”

Remove the trusted registration with:

```bash
make remove-codex-trusted
# or
make remove-claude-code-trusted
```

You may register both names simultaneously. They launch the same application,
but only the trusted registration sets `CHEQ_ENABLE_SNAPSHOT_LOOKUPS=1`. Choose
the server explicitly in sensitive tests so the access boundary is visible.

The trusted switch is not real authentication or RBAC. Any local user who can
edit the MCP configuration or read the source dataset can enable it. In
production, this capability would sit behind an authenticated remote MCP and an
authorization policy evaluated for every request.

### What do `make demo` and `make demo-trusted` do?

These targets are terminal smoke-test helpers; they do not install anything
into Codex or Claude Code.

```bash
make demo          # bootstrap, test, then start the regular STDIO server
make demo-trusted  # bootstrap, test, then start the trusted STDIO server
```

An MCP STDIO server waits for protocol messages on standard input, so it may
look idle when started directly in a terminal. For normal interactive use,
prefer one of the `make install-*` targets and let Codex or Claude Code start the
process. Press Ctrl+C to stop a directly launched demo server.

For a different local CSV snapshot, set `CHEQ_DATASET_PATH` before starting the
server. Protocol messages use stdout; diagnostics use stderr.

## Manual MCP configuration

The Makefile commands above are the easiest setup. The equivalent manual
configuration is shown here for inspection or clients where the Makefile cannot
be used. Replace the placeholder with the clone's absolute path.

### Regular Codex

Add to `~/.codex/config.toml`, or `.codex/config.toml` in a trusted clone:

```toml
[mcp_servers.cheq-churn]
command = "uv"
args = ["run", "--directory", "/ABSOLUTE/PATH/TO/cheq-churn-mcp", "cheq-churn-mcp"]
```

### Trusted-demo Codex

```toml
[mcp_servers.cheq-churn-trusted]
command = "uv"
args = ["run", "--directory", "/ABSOLUTE/PATH/TO/cheq-churn-mcp", "cheq-churn-mcp"]

[mcp_servers.cheq-churn-trusted.env]
CHEQ_ENABLE_SNAPSHOT_LOOKUPS = "1"
```

### Regular Claude Code

Create `.mcp.json` in the clone root, or merge this entry into an existing file:

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

### Trusted-demo Claude Code

```json
{
  "mcpServers": {
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
}
```

Run `make print-mcp-config` or `make print-mcp-config-trusted` to print
ready-to-paste entries using the current clone's absolute path. This is a local
STDIO server, so there is no hostname, listening port, or `0.0.0.0` address.

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

## Optional Docker runtime

Docker is not required for the assignment's normal local path. The
`make install-*` commands above run the MCP directly with `uv`.

The Dockerfile provides a reproducible alternative runtime: it packages the
Python application and dependencies into an image. DuckDB is embedded in the
application process, so there is no separate DuckDB container, database server,
port, or Docker Compose stack to start. One MCP process is the entire runtime.

The image deliberately excludes the customer dataset. Bootstrap it on the host,
build the image, and mount the local `data/` directory read-only at runtime:

```bash
make bootstrap
docker build --tag cheq-churn-mcp:local .
docker run --interactive --rm \
  --mount type=bind,source="$(pwd)/data",target=/app/data,readonly \
  cheq-churn-mcp:local
```

The flags matter:

- `--interactive` keeps stdin open because this MCP uses STDIO transport.
- `--rm` removes the stopped container; it does not delete the host dataset.
- `--mount ... readonly` makes the ignored host dataset visible at `/app/data`
  without copying it into the image or allowing the container to modify it.
- No `-p` flag is needed because the local server does not listen on a network
  port.

That command starts the regular aggregate-only server. To start the same image
with the trusted-demo tools enabled, pass the explicit environment variable:

```bash
docker run --interactive --rm \
  --env CHEQ_ENABLE_SNAPSHOT_LOOKUPS=1 \
  --mount type=bind,source="$(pwd)/data",target=/app/data,readonly \
  cheq-churn-mcp:local
```

These commands are useful for checking that the application runs in a clean,
reproducible environment. They still start an STDIO MCP process, so a directly
launched container may appear idle while it waits for protocol input. The
repository's Codex and Claude Code installation helpers intentionally use the
simpler `uv` runtime, not Docker.

For a CSV mounted at another container path, set `CHEQ_DATASET_PATH` to that
in-container path. Docker's bind-mount behavior is documented in the
[Docker storage guide](https://docs.docker.com/engine/storage/bind-mounts/).
