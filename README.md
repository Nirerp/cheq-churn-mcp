# CHEQ Churn Insights MCP

A local MCP server for asking safe, repeatable questions about the Telco Customer
Churn dataset from Codex or Claude Code.

It has two modes:

| Server | Use it for | Customer IDs |
| --- | --- | --- |
| `cheq-churn` | Normal aggregate questions: counts, churn rates, averages, and comparisons | Never exposed |
| `cheq-churn-trusted` | A local demonstration of privileged customer lookup workflows | Can discover up to 10 IDs and look up selected fields |

`cheq-churn-trusted` is a deliberately named local demo switch, **not real RBAC**.
Anyone who can edit the local MCP configuration can enable it. Use the regular
server by default.

## Run it in four steps

### 1. Install dependencies and download the dataset

Run these once after cloning:

```bash
uv sync --all-groups
make bootstrap
```

`make bootstrap` downloads the pinned 7,043-row dataset into the ignored
`data/` directory. The source dataset is intentionally not committed to Git.

### 2. Start it directly (optional smoke test)

Use this when you want to check that the server starts in a terminal:

```bash
# Regular, aggregate-only server
uv run cheq-churn-mcp

# Trusted local demo
CHEQ_ENABLE_SNAPSHOT_LOOKUPS=1 uv run cheq-churn-mcp
```

The process will look idle after it starts. That is expected: an STDIO MCP
server waits for an MCP client to send it messages. Press `Ctrl+C` to stop it.

For a smoke test that also runs the checks first, use `make demo` or
`make demo-trusted`.

### 3. Connect it to Codex or Claude Code

Choose **one** of the following registrations, then restart the client.

#### Regular server (recommended)

```bash
# Codex
make install-codex

# Claude Code
make install-claude-code
```

The registered MCP name is `cheq-churn`.

#### Trusted local demo

```bash
# Codex
make install-codex-trusted

# Claude Code
make install-claude-code-trusted
```

The registered MCP name is `cheq-churn-trusted`. It adds `find_customer_ids`
and `get_customer_snapshot` to the regular tools.

### 4. Check the registration and ask a question

```bash
# Codex
codex mcp get cheq-churn

# Claude Code
claude mcp get cheq-churn
```

Then ask, for example:

- “What percentage of customers churned?”
- “Which contract has the highest churn rate?”
- “How many churned customers said they don't know why?”

For the trusted demo only:

- “Using only `cheq-churn-trusted`, give me one customer ID for a customer who
  churned for an unclear reason.”

## Remove a local registration

```bash
# Regular server
make remove-codex
make remove-claude-code

# Trusted demo
make remove-codex-trusted
make remove-claude-code-trusted
```

## Manual configuration

The Make targets are the simplest option. If you need to add the MCP manually,
run one of these commands to print a ready-to-paste configuration using this
clone's absolute path:

```bash
make print-mcp-config
make print-mcp-config-trusted
```

The output contains both the Codex TOML entry and the Claude Code JSON entry.
This server uses STDIO, so there is no hostname, port, or `0.0.0.0` address.

## Optional Docker runtime

Docker is **not** needed for the normal local path above. It packages the same
MCP process into a reproducible image; DuckDB runs inside that process, so
there is no database container or Docker Compose stack.

```bash
make bootstrap
docker build --tag cheq-churn-mcp:local .

# Regular server
docker run --interactive --rm \
  --mount type=bind,source="$(pwd)/data",target=/app/data,readonly \
  cheq-churn-mcp:local

# Trusted local demo
docker run --interactive --rm \
  --env CHEQ_ENABLE_SNAPSHOT_LOOKUPS=1 \
  --mount type=bind,source="$(pwd)/data",target=/app/data,readonly \
  cheq-churn-mcp:local
```

These Docker commands **only start the MCP process**. They do **not** register
or connect it to Codex or Claude Code, so the container will wait on standard
input and appear idle. The `make install-*` commands intentionally use `uv`;
they are the recommended way to connect this local project to either client.

To use the Docker image with a client, configure that client to launch the
equivalent `docker run --interactive --rm ...` command as its STDIO MCP
command, including an absolute read-only mount for this clone's `data/`
directory. No network port is required.

## What the MCP can and cannot do

The regular server exposes three tools:

- `describe_dataset` — supported fields, metric definitions, source version,
  and limitations.
- `analyze_customers` — approved aggregate metrics, filters, and groupings.
- `data_quality_summary` — row count, uniqueness, and core completeness checks.

It rejects raw SQL and unsupported metrics, filters, or groupings with an
actionable `INVALID_ARGUMENT` error. An empty aggregate is returned as an empty
result, not an error. The regular server cannot discover customer IDs or return
individual customer records.

Every aggregate response includes the pinned dataset revision and applied
filters. Small grouped results are suppressed below five customers.

## Verify repository checks

```bash
uv run ruff check .
uv run pytest
```
