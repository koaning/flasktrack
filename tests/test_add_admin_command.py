"""Test the add-admin command with real database interactions."""

import subprocess
import sys

import pytest
from typer.testing import CliRunner

from flasktrack.cli import app

runner = CliRunner()


@pytest.fixture
def flask_project(tmp_path):
    """Create a real Flask project for testing."""
    # Use the init command to create a real project
    project_dir = tmp_path / "test_app"
    result = runner.invoke(app, ["init", "test-app", "--dir", str(project_dir)])

    # If init fails (e.g., template not available), skip the test
    if result.exit_code != 0:
        pytest.skip("Could not create Flask project for testing")

    # Install the required dependencies for the Flask app
    # We need to install the dependencies listed in the project's requirements
    requirements_file = project_dir / "requirements-in.txt"
    if requirements_file.exists():
        # Install dependencies using uv to the current environment
        # This is needed for the subprocess calls to work
        deps = requirements_file.read_text().strip().split("\n")
        # Filter out empty lines and comments
        deps = [d for d in deps if d and not d.startswith("#")]
        subprocess.run(
            ["uv", "pip", "install", "-q"] + deps, check=False, capture_output=True
        )

    return project_dir


def test_add_admin_creates_admin_user(flask_project):
    """Test that add-admin command creates a user with admin privileges."""
    # Add an admin user
    result = runner.invoke(
        app,
        [
            "add-admin",
            "adminuser",
            "admin@example.com",
            "--password",
            "admin123",
            "--app-path",
            str(flask_project),
        ],
    )

    # Debug output if test fails
    if result.exit_code != 0:
        print(f"Command failed with exit code {result.exit_code}")
        print(f"Output: {result.stdout}")
        if hasattr(result, "stderr"):
            print(f"Error: {result.stderr}")

    assert result.exit_code == 0, f"Command failed. Output: {result.stdout}"
    assert "Admin user 'adminuser' added successfully!" in result.stdout
    assert "Role: Administrator" in result.stdout

    # Verify the user exists in the database with admin flag
    # We'll create a script to check the database
    check_script = flask_project / "check_admin.py"
    check_script.write_text("""
import sys
from app import create_app, db
from app.models.user import User

app = create_app("development")
with app.app_context():
    user = User.query.filter_by(username="adminuser").first()
    if user:
        print(f"User found: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is admin: {user.is_admin}")
        sys.exit(0 if user.is_admin else 1)
    else:
        print("User not found")
        sys.exit(2)
""")

    # Run the check script
    result = subprocess.run(
        [sys.executable, str(check_script)],
        capture_output=True,
        text=True,
        cwd=str(flask_project),
    )

    assert result.returncode == 0, f"Admin flag not set. Output: {result.stdout}"
    assert "Is admin: True" in result.stdout


def test_add_admin_duplicate_user_fails(flask_project):
    """Test that adding a duplicate admin fails."""
    # Add first admin
    result = runner.invoke(
        app,
        [
            "add-admin",
            "duplicateuser",
            "dup@example.com",
            "--password",
            "pass123",
            "--app-path",
            str(flask_project),
        ],
    )
    assert result.exit_code == 0

    # Try to add the same username again
    result = runner.invoke(
        app,
        [
            "add-admin",
            "duplicateuser",
            "other@example.com",
            "--password",
            "pass456",
            "--app-path",
            str(flask_project),
        ],
    )

    assert result.exit_code == 1
    assert "Failed to add admin" in result.stdout


def test_add_admin_duplicate_email_fails(flask_project):
    """Test that adding an admin with duplicate email fails."""
    # Add first admin
    result = runner.invoke(
        app,
        [
            "add-admin",
            "user1",
            "same@example.com",
            "--password",
            "pass123",
            "--app-path",
            str(flask_project),
        ],
    )
    assert result.exit_code == 0

    # Try to add different username but same email
    result = runner.invoke(
        app,
        [
            "add-admin",
            "user2",
            "same@example.com",
            "--password",
            "pass456",
            "--app-path",
            str(flask_project),
        ],
    )

    assert result.exit_code == 1
    assert "Failed to add admin" in result.stdout


def test_add_admin_with_password_prompt(flask_project):
    """Test add-admin command with password prompting."""
    # Use password prompt instead of --password flag
    result = runner.invoke(
        app,
        [
            "add-admin",
            "promptuser",
            "prompt@example.com",
            "--app-path",
            str(flask_project),
        ],
        input="secretpass\nsecretpass\n",  # Password and confirmation
    )

    assert result.exit_code == 0
    assert "Admin user 'promptuser' added successfully!" in result.stdout

    # Verify the user can authenticate with the password
    check_script = flask_project / "check_password.py"
    check_script.write_text("""
import sys
from app import create_app, db
from app.models.user import User

app = create_app("development")
with app.app_context():
    user = User.query.filter_by(username="promptuser").first()
    if user and user.check_password("secretpass"):
        print("Password is correct")
        sys.exit(0)
    else:
        print("Password check failed")
        sys.exit(1)
""")

    result = subprocess.run(
        [sys.executable, str(check_script)],
        capture_output=True,
        text=True,
        cwd=str(flask_project),
    )

    assert result.returncode == 0
    assert "Password is correct" in result.stdout


def test_add_multiple_admins(flask_project):
    """Test adding multiple admin users."""
    admins = [
        ("admin1", "admin1@example.com", "pass1"),
        ("admin2", "admin2@example.com", "pass2"),
        ("admin3", "admin3@example.com", "pass3"),
    ]

    for username, email, password in admins:
        result = runner.invoke(
            app,
            [
                "add-admin",
                username,
                email,
                "--password",
                password,
                "--app-path",
                str(flask_project),
            ],
        )
        assert result.exit_code == 0
        assert f"Admin user '{username}' added successfully!" in result.stdout

    # Verify all admins exist in database
    check_script = flask_project / "check_all_admins.py"
    check_script.write_text("""
import sys
from app import create_app, db
from app.models.user import User

app = create_app("development")
with app.app_context():
    admins = User.query.filter_by(is_admin=True).all()
    print(f"Total admins: {len(admins)}")
    for admin in admins:
        print(f"- {admin.username} ({admin.email})")
    sys.exit(0 if len(admins) == 3 else 1)
""")

    result = subprocess.run(
        [sys.executable, str(check_script)],
        capture_output=True,
        text=True,
        cwd=str(flask_project),
    )

    assert result.returncode == 0
    assert "Total admins: 3" in result.stdout
    for username, _, _ in admins:
        assert username in result.stdout


def test_add_admin_no_flask_app(tmp_path):
    """Test add-admin command when no Flask app exists."""
    result = runner.invoke(
        app,
        [
            "add-admin",
            "testuser",
            "test@example.com",
            "--password",
            "password123",
            "--app-path",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "No Flask application found" in result.stdout


def test_add_admin_no_app_directory(tmp_path):
    """Test add-admin command when app directory is missing."""
    # Create app.py but no app directory
    (tmp_path / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")

    result = runner.invoke(
        app,
        [
            "add-admin",
            "testuser",
            "test@example.com",
            "--password",
            "password123",
            "--app-path",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "No 'app' directory found" in result.stdout


def test_regular_user_vs_admin(flask_project):
    """Test that we can distinguish between regular users and admin users."""
    # For this test, we need to create a regular user manually
    # since we don't have an add-user command anymore
    create_user_script = flask_project / "create_regular_user.py"
    create_user_script.write_text("""
import sys
from app import create_app, db
from app.models.user import User

app = create_app("development")
with app.app_context():
    db.create_all()

    # Create a regular user (is_admin defaults to False)
    user = User(username="regularuser", email="regular@example.com")
    user.set_password("regular123")
    # Don't set is_admin, it should default to False

    db.session.add(user)
    db.session.commit()
    print(f"Created regular user: {user.username}")
""")

    result = subprocess.run(
        [sys.executable, str(create_user_script)],
        capture_output=True,
        text=True,
        cwd=str(flask_project),
    )
    assert result.returncode == 0

    # Now add an admin user
    result = runner.invoke(
        app,
        [
            "add-admin",
            "adminuser",
            "admin@example.com",
            "--password",
            "admin123",
            "--app-path",
            str(flask_project),
        ],
    )
    assert result.exit_code == 0

    # Check both users and their admin status
    check_script = flask_project / "check_users.py"
    check_script.write_text("""
import sys
from app import create_app, db
from app.models.user import User

app = create_app("development")
with app.app_context():
    regular = User.query.filter_by(username="regularuser").first()
    admin = User.query.filter_by(username="adminuser").first()

    print(f"Regular user is_admin: {regular.is_admin if regular else 'Not found'}")
    print(f"Admin user is_admin: {admin.is_admin if admin else 'Not found'}")

    if regular and admin:
        if not regular.is_admin and admin.is_admin:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.exit(2)
""")

    result = subprocess.run(
        [sys.executable, str(check_script)],
        capture_output=True,
        text=True,
        cwd=str(flask_project),
    )

    assert result.returncode == 0
    assert "Regular user is_admin: False" in result.stdout
    assert "Admin user is_admin: True" in result.stdout
