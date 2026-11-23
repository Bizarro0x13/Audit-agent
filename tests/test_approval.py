import typer

from agent.approval import approve_all, cli_ask
from agent.schemas import Finding


def finding():
    return Finding(id="F-001", title="t", severity="low", file="a", line_start=1, line_end=1,
                   description="d", impact="i")


def test_cli_ask_accepts_y_n_s(monkeypatch):
    for typed, expected in [("y", "y"), ("N", "n"), ("skip", "s")]:
        monkeypatch.setattr(typer, "prompt", lambda *a, t=typed, **k: t)
        assert cli_ask(finding()) == expected


def test_cli_ask_repeats_until_valid(monkeypatch):
    answers = iter(["maybe", "", "y"])
    monkeypatch.setattr(typer, "prompt", lambda *a, **k: next(answers))
    assert cli_ask(finding()) == "y"


def test_approve_all_says_yes():
    assert approve_all(finding()) == "y"
