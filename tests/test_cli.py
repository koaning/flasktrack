"""Test CLI commands."""

from typer.testing import CliRunner

from flasktrack import __version__
from flasktrack.cli import app

runner = CliRunner()


def test_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__
