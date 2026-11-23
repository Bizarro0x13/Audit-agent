from pathlib import Path

import typer

app = typer.Typer(help="Reference audit agent.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Reference audit agent."""


@app.command()
def audit(path: Path) -> None:
    """Audit the code under PATH."""
    if not path.is_dir():
        typer.echo(f"error: {path} is not a directory", err=True)
        raise typer.Exit(code=2)
    typer.echo("not implemented")
