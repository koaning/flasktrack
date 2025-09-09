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


def test_routes_command(flask_app_file):
    """Test routes command."""
    result = runner.invoke(app, ["routes", str(flask_app_file)])
    assert result.exit_code == 0
    assert "Flask Routes" in result.stdout
    assert "/api/users" in result.stdout


