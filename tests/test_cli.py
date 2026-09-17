from typer.testing import CliRunner
from qanalisa.cli import app

runner = CliRunner()


def test_cli_help_mentions_qanalisa():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "QAnalisa" in result.stdout
