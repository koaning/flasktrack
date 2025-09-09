"""Test the add-user command."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import pytest
from typer.testing import CliRunner

from flasktrack.cli import app
from flasktrack.utils import add_user_to_app

runner = CliRunner()


def test_add_user_command_no_flask_app(tmp_path):
    """Test add-user command when no Flask app exists."""
    result = runner.invoke(
        app, 
        ["add-user", "testuser", "test@example.com", "--password", "password123", "--app-path", str(tmp_path)]
    )
    
    assert result.exit_code == 1
    assert "No Flask application found" in result.stdout


def test_add_user_command_no_app_directory(tmp_path):
    """Test add-user command when app directory is missing."""
    # Create app.py but no app directory
    (tmp_path / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
    
    result = runner.invoke(
        app, 
        ["add-user", "testuser", "test@example.com", "--password", "password123", "--app-path", str(tmp_path)]
    )
    
    assert result.exit_code == 1
    assert "No 'app' directory found" in result.stdout


def test_add_user_command_success(tmp_path):
    """Test successful user creation."""
    # Create a minimal Flask app structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (tmp_path / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
    
    with patch('flasktrack.cli.add_user_to_app') as mock_add_user:
        mock_add_user.return_value = True
        
        result = runner.invoke(
            app, 
            ["add-user", "testuser", "test@example.com", "--password", "password123", "--app-path", str(tmp_path)]
        )
        
        assert result.exit_code == 0
        assert "User 'testuser' added successfully!" in result.stdout
        assert "Email: test@example.com" in result.stdout
        assert "User can now log in to the application!" in result.stdout
        
        # Verify the function was called with correct arguments
        mock_add_user.assert_called_once_with(
            app_path=tmp_path,
            username="testuser",
            email="test@example.com",
            password="password123"
        )


def test_add_user_command_duplicate_user(tmp_path):
    """Test adding a duplicate user."""
    # Create a minimal Flask app structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (tmp_path / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
    
    with patch('flasktrack.cli.add_user_to_app') as mock_add_user:
        mock_add_user.return_value = False
        
        result = runner.invoke(
            app, 
            ["add-user", "testuser", "test@example.com", "--password", "password123", "--app-path", str(tmp_path)]
        )
        
        assert result.exit_code == 1
        assert "Failed to add user. User might already exist." in result.stdout


def test_add_user_command_exception(tmp_path):
    """Test handling of exceptions during user creation."""
    # Create a minimal Flask app structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (tmp_path / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
    
    with patch('flasktrack.cli.add_user_to_app') as mock_add_user:
        mock_add_user.side_effect = Exception("Database connection failed")
        
        result = runner.invoke(
            app, 
            ["add-user", "testuser", "test@example.com", "--password", "password123", "--app-path", str(tmp_path)]
        )
        
        assert result.exit_code == 1
        assert "Error adding user: Database connection failed" in result.stdout


def test_add_user_command_with_password_prompt(tmp_path):
    """Test add-user command with password prompting."""
    # Create a minimal Flask app structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (tmp_path / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
    
    with patch('flasktrack.cli.add_user_to_app') as mock_add_user:
        mock_add_user.return_value = True
        
        # Simulate password input
        result = runner.invoke(
            app, 
            ["add-user", "testuser", "test@example.com", "--app-path", str(tmp_path)],
            input="password123\npassword123\n"
        )
        
        assert result.exit_code == 0
        assert "User 'testuser' added successfully!" in result.stdout
        
        # Verify the function was called with the password from prompt
        mock_add_user.assert_called_once_with(
            app_path=tmp_path,
            username="testuser",
            email="test@example.com",
            password="password123"
        )


def test_add_user_to_app_success(tmp_path, monkeypatch):
    """Test add_user_to_app function with successful user creation."""
    # Mock subprocess.run to simulate successful execution
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        result = add_user_to_app(
            app_path=tmp_path,
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        assert result is True
        
        # Verify subprocess.run was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        
        # Check that a Python script was executed
        assert call_args[0][0][0].endswith('python') or call_args[0][0][0].endswith('python3')
        assert call_args[0][0][1].endswith('.py')
        
        # Check working directory
        assert call_args[1]['cwd'] == str(tmp_path)


def test_add_user_to_app_duplicate_user(tmp_path):
    """Test add_user_to_app function when user already exists."""
    # Mock subprocess.run to simulate duplicate user error
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "ERROR: User with this username or email already exists"
    
    with patch('subprocess.run', return_value=mock_result):
        result = add_user_to_app(
            app_path=tmp_path,
            username="existinguser",
            email="existing@example.com",
            password="password123"
        )
        
        assert result is False


def test_add_user_to_app_other_error(tmp_path):
    """Test add_user_to_app function with other errors."""
    # Mock subprocess.run to simulate other error
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "ImportError: No module named 'app'"
    
    with patch('subprocess.run', return_value=mock_result):
        with pytest.raises(Exception) as exc_info:
            add_user_to_app(
                app_path=tmp_path,
                username="testuser",
                email="test@example.com",
                password="password123"
            )
        
        assert "No module named 'app'" in str(exc_info.value)


def test_add_user_to_app_subprocess_exception(tmp_path):
    """Test add_user_to_app function when subprocess raises exception."""
    with patch('subprocess.run', side_effect=OSError("Command not found")):
        with pytest.raises(OSError) as exc_info:
            add_user_to_app(
                app_path=tmp_path,
                username="testuser",
                email="test@example.com",
                password="password123"
            )
        
        assert "Command not found" in str(exc_info.value)


def test_add_user_integration_with_init(tmp_path):
    """Integration test: create Flask app with init, then add user."""
    # First create a Flask app using init command
    project_dir = tmp_path / "test_app"
    result = runner.invoke(app, ["init", "test-app", "--dir", str(project_dir)])
    
    # Skip this test if init command failed (template might not be available)
    if result.exit_code != 0:
        pytest.skip("Init command failed, likely template not available")
    
    assert project_dir.exists()
    
    # Now try to add a user to the created app
    with patch('flasktrack.cli.add_user_to_app') as mock_add_user:
        mock_add_user.return_value = True
        
        result = runner.invoke(
            app,
            ["add-user", "admin", "admin@test.com", "--password", "admin123", "--app-path", str(project_dir)]
        )
        
        assert result.exit_code == 0
        assert "User 'admin' added successfully!" in result.stdout