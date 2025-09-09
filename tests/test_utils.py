"""Test utility functions."""

import tempfile
from pathlib import Path

from flasktrack.utils import format_size, get_project_info, validate_flask_app


def test_format_size():
    """Test size formatting."""
    assert format_size(100) == "100.0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1024) == "1.0 MB"
    assert format_size(1024 * 1024 * 1024) == "1.0 GB"
    assert format_size(1536) == "1.5 KB"


def test_get_project_info_file(flask_app_file):
    """Test getting project info for a file."""
    info = get_project_info(flask_app_file)

    assert info["exists"] is True
    assert info["type"] == "file"
    assert info["name"] == flask_app_file.name
    assert "size" in info


def test_get_project_info_directory(tmp_path):
    """Test getting project info for a directory."""
    (tmp_path / "app.py").write_text("print('hello')")
    (tmp_path / "test.py").write_text("print('test')")

    info = get_project_info(tmp_path)

    assert info["exists"] is True
    assert info["type"] == "directory"
    assert info["python_files"] == 2


def test_get_project_info_nonexistent():
    """Test getting project info for non-existent path."""
    info = get_project_info(Path("/nonexistent/path"))

    assert info["exists"] is False


def test_validate_flask_app_valid():
    """Test validating a valid Flask app file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("from flask import Flask\napp = Flask(__name__)")
        temp_path = Path(f.name)

    try:
        assert validate_flask_app(temp_path) is True
    finally:
        temp_path.unlink()


def test_validate_flask_app_import_style():
    """Test validating Flask app with different import style."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import flask\napp = flask.Flask(__name__)")
        temp_path = Path(f.name)

    try:
        assert validate_flask_app(temp_path) is True
    finally:
        temp_path.unlink()


def test_validate_flask_app_invalid():
    """Test validating an invalid Flask app file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("print('not a flask app')")
        temp_path = Path(f.name)

    try:
        assert validate_flask_app(temp_path) is False
    finally:
        temp_path.unlink()


def test_validate_flask_app_nonexistent():
    """Test validating non-existent file."""
    assert validate_flask_app(Path("/nonexistent.py")) is False


def test_validate_flask_app_wrong_extension():
    """Test validating file with wrong extension."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("from flask import Flask")
        temp_path = Path(f.name)

    try:
        assert validate_flask_app(temp_path) is False
    finally:
        temp_path.unlink()
