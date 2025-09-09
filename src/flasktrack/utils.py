"""Utility functions for FlaskTrack."""

import os
import sys
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


def add_user_to_app(app_path: Path, username: str, email: str, password: str) -> bool:
    """Add a new user to a Flask application database.

    Args:
        app_path: Path to the Flask application directory
        username: Username for the new user
        email: Email address for the new user
        password: Password for the new user

    Returns:
        True if user was added successfully, False otherwise
    """
    import subprocess
    import tempfile

    # Create a Python script to add the user
    # We use a temp file to execute database operations in the target Flask app's
    # context, avoiding import conflicts and ensuring proper isolation between
    # the FlaskTrack process and the target application's environment
    script_content = f'''
import sys
import os
sys.path.insert(0, "{app_path}")
os.chdir("{app_path}")

# Set environment to development to use SQLite
os.environ["FLASK_ENV"] = "development"

from app import create_app, db
from app.models.user import User

# Create app context
app = create_app("development")

with app.app_context():
    # Ensure database and tables exist
    db.create_all()

    # Check if user already exists
    existing_user = User.query.filter(
        (User.username == "{username}") | (User.email == "{email}")
    ).first()

    if existing_user:
        print("ERROR: User with this username or email already exists", file=sys.stderr)
        sys.exit(1)

    # Create new user
    user = User(username="{username}", email="{email}")
    user.set_password("{password}")

    # Add and commit
    db.session.add(user)
    db.session.commit()

    print(f"User '{{user.username}}' created successfully")
'''

    # Write script to temporary file and execute it
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script_content)
        temp_script = f.name

    try:
        # Run the script in the app's Python environment
        result = subprocess.run(
            [sys.executable, temp_script],
            capture_output=True,
            text=True,
            cwd=str(app_path),
        )

        # Clean up temp file
        os.unlink(temp_script)

        if result.returncode == 0:
            return True
        else:
            # Check if it's a duplicate user error
            if "already exists" in result.stderr:
                return False
            # For other errors, raise an exception with the error message
            raise Exception(result.stderr or "Unknown error occurred")

    except Exception as e:
        # Clean up temp file if it still exists
        if os.path.exists(temp_script):
            os.unlink(temp_script)
        raise e
