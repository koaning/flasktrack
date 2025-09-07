"""Test CLI commands."""

from typer.testing import CliRunner

from flasktrack.cli import app
from flasktrack import __version__


runner = CliRunner()


def test_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_routes_command(flask_app_file):
    """Test routes command."""
    result = runner.invoke(app, ["routes", str(flask_app_file)])
    assert result.exit_code == 0
    assert "Flask Routes" in result.stdout
    assert "/api/users" in result.stdout


def test_analyze_command(flask_app_file):
    """Test analyze command."""
    result = runner.invoke(app, ["analyze", str(flask_app_file)])
    assert result.exit_code == 0
    assert "Flask Application Analysis" in result.stdout
    assert "total_routes" in result.stdout


def test_analyze_with_output(flask_app_file, tmp_path):
    """Test analyze command with output file."""
    output_file = tmp_path / "analysis.json"
    result = runner.invoke(
        app, 
        ["analyze", str(flask_app_file), "--output", str(output_file)]
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert "Analysis saved to" in result.stdout


def test_track_command_help():
    """Test track command help."""
    result = runner.invoke(app, ["track", "--help"])
    assert result.exit_code == 0
    assert "Track a Flask application" in result.stdout