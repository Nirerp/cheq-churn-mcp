.PHONY: bootstrap check demo

bootstrap:
	test -f data/telco_customer_churn.csv || uv run python scripts/bootstrap_data.py

check:
	uv run ruff check .
	uv run pytest

demo: bootstrap check
	uv run cheq-churn-mcp
