"""Ways to get a human decision on a finding. An 'ask' function maps a Finding to y / n / s."""

import typer

from agent.schemas import Finding


def show(f: Finding) -> None:
    typer.echo(f"\n=== {f.id} [{f.severity.value}] {f.title}")
    typer.echo(f"Location: {f.file}:{f.line_start}-{f.line_end}")
    typer.echo(f"Description: {f.description}")
    typer.echo(f"Impact: {f.impact}")
    typer.echo(f"Verifier ({f.status.value}): {f.verifier_note or 'not verified'}")


def cli_ask(f: Finding) -> str:
    """Interactive: show the finding and ask the person. Repeats until the answer is valid."""
    show(f)
    while True:
        answer = typer.prompt("Approve this finding? [y]es / [n]o / [s]kip").strip().lower()[:1]
        if answer in ("y", "n", "s"):
            return answer
        typer.echo("Please answer y, n or s.")


def approve_all(f: Finding) -> str:
    """Only for automated evaluation. Reports say the findings were auto-approved."""
    return "y"
