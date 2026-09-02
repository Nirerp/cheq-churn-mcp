.PHONY: bootstrap check demo demo-trusted print-mcp-config install-codex remove-codex install-claude-code remove-claude-code

MCP_NAME := cheq-churn
PROJECT_ROOT := $(shell pwd -P)

bootstrap:
	test -f data/telco_customer_churn.csv || uv run python scripts/bootstrap_data.py

check:
	uv run ruff check .
	uv run pytest

demo: bootstrap check
	uv run cheq-churn-mcp

demo-trusted: bootstrap check
	CHEQ_ENABLE_SNAPSHOT_LOOKUPS=1 uv run cheq-churn-mcp

print-mcp-config:
	@printf '%s\n' '[mcp_servers.$(MCP_NAME)]' 'command = "uv"' \
		'args = ["run", "--directory", "$(PROJECT_ROOT)", "cheq-churn-mcp"]'
	@printf '%s\n' '' '{' '  "mcpServers": {' '    "$(MCP_NAME)": {' \
		'      "command": "uv",' \
		'      "args": ["run", "--directory", "$(PROJECT_ROOT)", "cheq-churn-mcp"]' \
		'    }' '  }' '}'

install-codex:
	@if codex mcp get $(MCP_NAME) >/dev/null 2>&1; then \
		echo 'Codex server "$(MCP_NAME)" already exists; inspect it with: codex mcp get $(MCP_NAME)' >&2; \
		exit 1; \
	fi
	codex mcp add $(MCP_NAME) -- uv run --directory "$(PROJECT_ROOT)" cheq-churn-mcp

remove-codex:
	codex mcp remove $(MCP_NAME)

install-claude-code:
	@command -v claude >/dev/null 2>&1 || { \
		echo 'Claude Code CLI is not installed or is not on PATH.' >&2; \
		exit 1; \
	}
	claude mcp add $(MCP_NAME) -- uv run --directory "$(PROJECT_ROOT)" cheq-churn-mcp

remove-claude-code:
	@command -v claude >/dev/null 2>&1 || { \
		echo 'Claude Code CLI is not installed or is not on PATH.' >&2; \
		exit 1; \
	}
	claude mcp remove $(MCP_NAME)
