"""Test the init command."""

import os
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from flasktrack.cli import app

runner = CliRunner()


def test_init_command_creates_project():
    """Test that init command creates a Flask project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_app"
        result = runner.invoke(app, ["init", "test-app", "--dir", str(project_dir)])

        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.stdout}")
            print(f"Exception: {result.exception}")

        assert result.exit_code == 0
        assert "Creating Flask application: test-app" in result.stdout
        assert "Project created at:" in result.stdout
        assert "Your Flask app is ready!" in result.stdout

        # Check that project directory was created
        assert project_dir.exists()
        assert project_dir.is_dir()

        # Check for key files and directories
        assert (project_dir / "app").exists()
        assert (project_dir / "app" / "__init__.py").exists()
        assert (project_dir / "app" / "models").exists()
        assert (project_dir / "app" / "models" / "user.py").exists()
        assert (project_dir / "app" / "controllers").exists()
        assert (project_dir / "app" / "controllers" / "auth.py").exists()
        assert (project_dir / "app" / "forms").exists()
        assert (project_dir / "app" / "forms" / "auth.py").exists()
        assert (project_dir / "app" / "views").exists()
        assert (project_dir / "app" / "static").exists()
        assert (project_dir / "app" / "config.py").exists()
        assert (project_dir / "tests").exists()
        assert (project_dir / "requirements.txt").exists()
        assert (project_dir / "requirements-dev.txt").exists()
        assert (project_dir / "requirements-in.txt").exists()
        assert (project_dir / "requirements-dev-in.txt").exists()
        assert (project_dir / "app.py").exists()
        assert (project_dir / ".env").exists()
        assert (project_dir / ".gitignore").exists()
        assert (project_dir / "README.md").exists()
        assert (project_dir / "justfile").exists()
        assert (project_dir / "data").exists()
        assert (project_dir / "data" / ".gitkeep").exists()


def test_init_command_with_spaces_in_name():
    """Test that init command handles project names with spaces."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "my_flask_app"
        result = runner.invoke(app, ["init", "My Flask App", "--dir", str(project_dir)])

        assert result.exit_code == 0

        # Check that project directory was created
        assert project_dir.exists()


def test_init_command_in_current_directory():
    """Test that init command works without --dir option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            result = runner.invoke(app, ["init", "test-app"])

            assert result.exit_code == 0

            # Check that project was created in current directory
            project_dir = Path(tmpdir) / "test_app"
            assert project_dir.exists()
        finally:
            # Restore original directory
            os.chdir(original_cwd)


def test_init_command_file_contents():
    """Test that generated files have correct content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "testproject"
        result = runner.invoke(app, ["init", "TestProject", "--dir", str(project_dir)])

        assert result.exit_code == 0

        # Check that app factory imports are correct
        app_init = (project_dir / "app" / "__init__.py").read_text()
        assert "from flask import Flask" in app_init
        assert "from flask_sqlalchemy import SQLAlchemy" in app_init
        assert "from flask_login import LoginManager" in app_init
        assert "def create_app(" in app_init

        # Check User model
        user_model = (project_dir / "app" / "models" / "user.py").read_text()
        assert "class User(UserMixin, db.Model):" in user_model
        assert "def set_password(self, password):" in user_model
        assert "def check_password(self, password):" in user_model

        # Check auth forms
        auth_forms = (project_dir / "app" / "forms" / "auth.py").read_text()
        assert "class LoginForm(FlaskForm):" in auth_forms
        assert "class RegistrationForm(FlaskForm):" in auth_forms

        # Check requirements-in files
        requirements_in = (project_dir / "requirements-in.txt").read_text()
        assert "Flask>=3.0.0" in requirements_in
        assert "Flask-SQLAlchemy>=3.1.0" in requirements_in
        assert "Flask-Login>=0.6.0" in requirements_in
        assert "Flask-WTF>=1.2.0" in requirements_in

        # Check dev requirements-in
        dev_requirements_in = (project_dir / "requirements-dev-in.txt").read_text()
        assert "pytest>=8.0.0" in dev_requirements_in
        assert "ruff>=0.1.0" in dev_requirements_in
        assert "black" not in dev_requirements_in

        # Check justfile
        justfile = (project_dir / "justfile").read_text()
        assert "install:" in justfile
        assert "run:" in justfile
        assert "test:" in justfile
        assert "uv pip compile" in justfile
        assert "uv pip sync" in justfile
        assert "uv run flask" in justfile
        assert "mkdir -p data" in justfile
        assert "ruff format" in justfile
        assert "ruff check" in justfile
        assert "black" not in justfile
        # Verify host is set to localhost instead of 0.0.0.0
        assert "--host=127.0.0.1" in justfile
        assert "--host=0.0.0.0" not in justfile

        # Check app.py has correct host configuration
        app_py = (project_dir / "app.py").read_text()
        assert 'host="127.0.0.1"' in app_py
        assert 'host="0.0.0.0"' not in app_py


def test_init_command_requires_project_name():
    """Test that init command requires project name and fails without it."""
    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert "Missing argument 'PROJECT_NAME'" in result.stdout
    assert "flasktrack init [PROJECT_NAME]" in result.stdout


def test_init_command_with_dot_uses_directory_name():
    """Test that init command with '.' uses current directory name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a subdirectory with a specific name
        test_dir = Path(tmpdir) / "my-awesome-app"
        test_dir.mkdir()

        # Change to that directory
        original_cwd = os.getcwd()
        os.chdir(str(test_dir))

        try:
            result = runner.invoke(app, ["init", "."])

            assert result.exit_code == 0
            assert "Using current directory name: my-awesome-app" in result.stdout
            assert "Creating Flask application: my-awesome-app" in result.stdout

            # Check that project was created in current directory
            project_dir = (
                test_dir / "my_awesome_app"
            )  # cookiecutter converts hyphens to underscores
            assert project_dir.exists()
            assert (project_dir / "app").exists()
            assert (project_dir / "justfile").exists()
        finally:
            # Restore original directory
            os.chdir(original_cwd)


def test_generated_project_flask_app_works():
    """Test that generated project Flask app structure is correct."""
    import sys

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "flask_integration_test"
        result = runner.invoke(
            app, ["init", "Flask Integration Test", "--dir", str(project_dir)]
        )

        assert result.exit_code == 0

        # Add the generated project to Python path
        sys.path.insert(0, str(project_dir))

        try:
            # Check that the app module structure is correct
            assert (project_dir / "app" / "__init__.py").exists()
            assert (project_dir / "app" / "models" / "user.py").exists()
            assert (project_dir / "app" / "controllers" / "auth.py").exists()
            assert (project_dir / "app" / "controllers" / "main.py").exists()

            # Read and verify the app factory function exists
            app_init_content = (project_dir / "app" / "__init__.py").read_text()
            assert "def create_app" in app_init_content
            assert "from flask import Flask" in app_init_content
            assert "from flask_bcrypt import Bcrypt" in app_init_content

            # Verify requirements are properly set up
            requirements_content = (project_dir / "requirements.txt").read_text()
            assert "flask==" in requirements_content.lower()
            assert "flask-bcrypt==" in requirements_content.lower()
            assert "flask-login==" in requirements_content.lower()

        finally:
            # Clean up Python path
            if str(project_dir) in sys.path:
                sys.path.remove(str(project_dir))
