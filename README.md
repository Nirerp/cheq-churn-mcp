# CHEQ Churn Insights MCP

A local MCP server for asking questions about the Telco Customer Churn dataset
from Codex or Claude Code.

- `cheq-churn` is the regular, aggregate-only server. It answers counts, churn
  rates, averages, and comparisons. It never returns customer IDs.
- `cheq-churn-trusted` is a local demo of privileged lookup workflows. It can
  discover up to 10 IDs and return selected customer fields. It is **not real
  RBAC**: any local user who can edit the MCP configuration can enable it.

## Follow these steps to talk to the MCP

### 1. Clone the repository

```bash
git clone https://github.com/Nirerp/cheq-churn-mcp.git
cd cheq-churn-mcp
```

### 2. Install dependencies and download the dataset

```bash
uv sync --all-groups
make bootstrap
```

`make bootstrap` downloads the pinned 7,043-row dataset into the ignored
`data/` directory. It is not committed to Git.

### 3. Run the demo

In a terminal, start the mode you want to test:

```bash
# Regular server: bootstrap, run checks, then start FastMCP
make demo

# Trusted local demo: bootstrap, run checks, then start FastMCP with lookup tools
make demo-trusted
```

The server will look idle because it is waiting for STDIO MCP messages. Press
`Ctrl+C` to stop it before the next step: Codex and Claude Code start their own
STDIO process.

### 4. Register the MCP with Codex or Claude Code

#### Regular server (recommended)

```bash
# Codex
make install-codex

# Claude Code
make install-claude-code
```

#### Trusted local demo

```bash
# Codex
make install-codex-trusted

# Claude Code
make install-claude-code-trusted
```

These commands register an STDIO server and tell the client how to start it.
They do not start a long-running service in your terminal.

### 5. Restart Codex or Claude Code

The newly registered MCP tools are loaded when the client starts.

### 6. Ask a question

Regular server examples:

- “What percentage of customers churned?”
- “Which contract has the highest churn rate?”
- “How many churned customers said they don't know why?”

Trusted-demo example:

- “Using only `cheq-churn-trusted`, give me one customer ID for a customer who
  churned for an unclear reason.”

## Docker: what it does and does not do

Docker is optional. It packages the same MCP process into an image; DuckDB runs
inside that process, so there is no database container, network port, or Docker
Compose stack.

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

After testing the container, press `Ctrl+C`, then register the MCP with the
client you want to use:

```bash
# Regular server
make install-codex
make install-claude-code

# Trusted local demo
make install-codex-trusted
make install-claude-code-trusted
```

Those commands **only start an MCP process in a container**. They do not connect
it to Codex or Claude Code, and the container will wait on standard input.

The `make install-*` commands above connect the client by having it launch the
`uv` version of the server. They do **not** attach Codex or Claude Code to the
container you just ran; STDIO does not work that way.

To make a client launch the Docker image instead, add a manual STDIO MCP entry
whose command is `docker run --interactive --rm ...`, with an absolute,
read-only mount of this clone's `data/` directory. No port is required.

## Remove a local registration

```bash
# Regular server
make remove-codex
make remove-claude-code

# Trusted demo
make remove-codex-trusted
make remove-claude-code-trusted
```

## Manual configuration and supported tools

Run `make print-mcp-config` or `make print-mcp-config-trusted` to print
ready-to-paste Codex and Claude Code configuration for the `uv` runtime.

The regular server exposes:

- `describe_dataset` — supported fields, metric definitions, source version,
  and limitations.
- `analyze_customers` — approved aggregate metrics, filters, and groupings.
- `data_quality_summary` — row count, uniqueness, and core completeness checks.

It rejects raw SQL and unsupported metrics, filters, or groupings with an
actionable `INVALID_ARGUMENT` error. Empty aggregate results are valid and
return an empty result. Small grouped results are suppressed below five
customers.

## Verify repository checks

```bash
uv run ruff check .
uv run pytest
```
