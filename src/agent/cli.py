import uuid
from pathlib import Path

import typer

from agent.env import load_env

app = typer.Typer(help="Reference audit agent.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Reference audit agent."""
    load_env()


@app.command()
def audit(
    path: Path,
    report: Path = Path("report.md"),
    approve_all: bool = typer.Option(
        False, help="Auto-approve every finding. For automated evaluation only."
    ),
) -> None:
    """Audit the code under PATH."""
    if not path.is_dir():
        typer.echo(f"error: {path} is not a directory", err=True)
        raise typer.Exit(code=2)

    from agent.approval import approve_all as ask_yes
    from agent.approval import cli_ask
    from agent.graph import build_graph
    from agent.models import CostCapExceeded, Model
    from agent.store import Store
    from agent.tools.files import FileTools

    run_id = uuid.uuid4().hex[:8]
    store = Store(".agent/runs.db")
    store.start_run(run_id, str(path))
    model = Model(store, run_id)
    tools = FileTools(path, store, run_id)
    graph = build_graph(model, tools, store, ask_yes if approve_all else cli_ask, report_path=report)
    try:
        result = graph.invoke(
            {"run_id": run_id, "target_root": str(path), "auto_approved": approve_all}
        )
    except CostCapExceeded as exc:
        typer.echo(f"stopped: {exc}", err=True)
        raise typer.Exit(code=3) from exc
    typer.echo(
        f"run {run_id}: {len(result.get('approved_ids', []))} approved of {len(result.get('findings', []))} findings, "
        f"cost ${store.run_cost(run_id):.4f}, report at {report}"
    )
