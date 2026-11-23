
from typer.testing import CliRunner

from agent.cli import app

runner = CliRunner()


def test_audit_rejects_missing_dir():
    result = runner.invoke(app, ["audit", "/no/such/dir"])
    assert result.exit_code == 2
