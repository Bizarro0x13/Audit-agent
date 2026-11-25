.PHONY: test lint eval eval-dry
test:
	uv run pytest -q
lint:
	uv run ruff check
eval:
	uv run python eval/run_eval.py

eval-dry:
	uv run python eval/run_eval.py --dry-run --split all --repeats 1 --variants single,graph_verify
