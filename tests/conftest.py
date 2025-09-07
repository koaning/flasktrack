"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest
from flask import Flask


@pytest.fixture
def sample_flask_app():
    """Create a sample Flask application for testing."""
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        return "Hello, World!"
    
    @app.route("/api/users")
    def users():
        return {"users": []}
    
    @app.route("/api/users/<int:user_id>")
    def user_detail(user_id):
        return {"id": user_id}
    
    @app.route("/api/data", methods=["GET", "POST"])
    def data():
        return {"data": "sample"}
    
    return app


@pytest.fixture
def flask_app_file(sample_flask_app):
    """Create a temporary Flask app file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello, World!"

@app.route("/api/users")
def users():
    return {"users": []}

@app.route("/api/users/<int:user_id>")
def user_detail(user_id):
    return {"id": user_id}

@app.route("/api/data", methods=["GET", "POST"])
def data():
    return {"data": "sample"}
""")
        temp_path = Path(f.name)
    
    yield temp_path
    
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def flask_factory_file():
    """Create a temporary Flask factory file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        return "Factory App"
    
    return app
""")
        temp_path = Path(f.name)
    
    yield temp_path
    
    temp_path.unlink(missing_ok=True)