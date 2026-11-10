from typer.testing import CliRunner
from findex.__main__ import app

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Findex Search Engine" in result.stdout
