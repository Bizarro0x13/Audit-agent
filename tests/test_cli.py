from pathlib import Path

from typer.testing import CliRunner

from agent.cli import app

runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "vault"


def test_audit_stub_runs():
    result = runner.invoke(app, ["audit", str(FIXTURE)])
    assert result.exit_code == 0
    assert "not implemented" in result.output


def test_audit_rejects_missing_dir():
    result = runner.invoke(app, ["audit", "/no/such/dir"])
    assert result.exit_code == 2
