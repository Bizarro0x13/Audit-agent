import sqlite3
import uuid
from pathlib import Path

import typer

from agent.env import load_env
from agent.rag import from_env

DB_PATH = ".agent/runs.db"

app = typer.Typer(help="Reference audit agent.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Reference audit agent."""
    load_env()


def _execute(run_id, target, report, approve_all, initial):
    """Run (initial state) or resume (initial=None) the graph for run_id."""
    from langgraph.checkpoint.sqlite import SqliteSaver

    from agent.approval import approve_all as ask_yes
    from agent.approval import cli_ask
    from agent.graph import build_graph
    from agent.models import CostCapExceeded, Model
    from agent.store import Store
    from agent.tools.files import FileTools

    store = Store(DB_PATH)
    if initial is not None:
        store.start_run(run_id, str(target))
    saver = SqliteSaver(sqlite3.connect(DB_PATH, check_same_thread=False))
    graph = build_graph(
        Model(store, run_id),
        FileTools(target, store, run_id),
        store,
        ask_yes if approve_all else cli_ask,
        report_path=report,
        checkpointer=saver,
        rag=from_env(),
    )
    config = {"configurable": {"thread_id": run_id}}
    try:
        result = graph.invoke(initial, config)
    except CostCapExceeded as exc:
        store.set_status(run_id, "failed")
        typer.echo(f"stopped: {exc}\nresume with: agent resume {run_id}", err=True)
        raise typer.Exit(code=3) from exc
    except (Exception, KeyboardInterrupt, typer.Abort) as exc:
        store.set_status(run_id, "failed")
        typer.echo(f"\nrun {run_id} stopped ({type(exc).__name__}).\n"
                   f"resume with: agent resume {run_id}", err=True)
        raise typer.Exit(code=1) from exc
    store.set_status(run_id, "done")
    typer.echo(
        f"run {run_id}: {len(result.get('approved_ids', []))} approved of "
        f"{len(result.get('findings', []))} findings, "
        f"cost ${store.run_cost(run_id):.4f}, report at {report}"
    )


APPROVE_ALL = typer.Option(False, help="Auto-approve every finding. For automated evaluation only.")


@app.command()
def audit(
    path: Path,
    report: Path = Path("report.md"),
    approve_all: bool = APPROVE_ALL,
) -> None:
    """Audit the code under PATH."""
    if not path.is_dir():
        typer.echo(f"error: {path} is not a directory", err=True)
        raise typer.Exit(code=2)
    run_id = uuid.uuid4().hex[:8]
    _execute(run_id, path, report, approve_all,
             {"run_id": run_id, "target_root": str(path), "auto_approved": approve_all})


@app.command()
def resume(
    run_id: str,
    report: Path = Path("report.md"),
    approve_all: bool = APPROVE_ALL,
) -> None:
    """Continue a stopped run from its last checkpoint (no finished step is repeated)."""
    from agent.store import Store

    row = Store(DB_PATH).get_run(run_id)
    if row is None:
        typer.echo(f"error: unknown run {run_id}", err=True)
        raise typer.Exit(code=2)
    target, status = row
    if status == "done":
        typer.echo(f"run {run_id} is already finished")
        raise typer.Exit(code=0)
    _execute(run_id, Path(target), report, approve_all, None)
