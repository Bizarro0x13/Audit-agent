.PHONY: test lint eval
test:
	uv run pytest -q
lint:
	uv run ruff check
eval:
	uv run python eval/run_eval.py
