"""Utility functions for FlaskTrack."""

from pathlib import Path
from typing import Any


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_project_info(project_path: Path) -> dict[str, Any]:
    """Get information about a Flask project.

    Args:
        project_path: Path to the project directory

    Returns:
        Dictionary containing project information
    """
    info = {
        "path": str(project_path),
        "name": project_path.name,
        "exists": project_path.exists(),
    }

    if project_path.is_file():
        info["type"] = "file"
        info["size"] = format_size(project_path.stat().st_size)
    elif project_path.is_dir():
        info["type"] = "directory"
        py_files = list(project_path.glob("**/*.py"))
        info["python_files"] = len(py_files)

    return info


def validate_flask_app(app_path: Path) -> bool:
    """Validate if a path contains a Flask application.

    Args:
        app_path: Path to check for Flask app

    Returns:
        True if valid Flask app found, False otherwise
    """
    if not app_path.exists():
        return False

    if app_path.is_file() and app_path.suffix == ".py":
        content = app_path.read_text()
        return "from flask import" in content or "import flask" in content

    return False
