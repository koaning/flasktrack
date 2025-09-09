"""Test Flask tracker functionality."""

import json
from pathlib import Path

import pytest

from flasktrack.tracker import FlaskTracker


def test_tracker_initialization(flask_app_file):
    """Test tracker initialization with Flask app file."""
    tracker = FlaskTracker(flask_app_file)
    assert tracker.app is not None
    assert tracker.app.name == "flask_app"


def test_tracker_with_factory(flask_factory_file):
    """Test tracker with Flask factory pattern."""
    tracker = FlaskTracker(flask_factory_file)
    assert tracker.app is not None


def test_get_routes(flask_app_file):
    """Test getting routes from Flask app."""
    tracker = FlaskTracker(flask_app_file)
    routes = tracker.get_routes()

    assert len(routes) == 5

    route_rules = [r["rule"] for r in routes]
    assert "/" in route_rules
    assert "/api/users" in route_rules
    assert "/api/users/<int:user_id>" in route_rules
    assert "/api/data" in route_rules

    data_route = next(r for r in routes if r["rule"] == "/api/data")
    assert "GET" in data_route["methods"]
    assert "POST" in data_route["methods"]


def test_analyze(flask_app_file):
    """Test Flask app analysis."""
    tracker = FlaskTracker(flask_app_file)
    analysis = tracker.analyze()

    assert analysis["total_routes"] == 5
    assert analysis["app_name"] == "flask_app"
    assert analysis["debug_mode"] is False
    assert analysis["testing_mode"] is False
    assert analysis["total_blueprints"] == 0
    assert "config_keys" in analysis


def test_save_analysis(flask_app_file, tmp_path):
    """Test saving analysis to file."""
    tracker = FlaskTracker(flask_app_file)
    analysis = tracker.analyze()

    output_file = tmp_path / "test_analysis.json"
    tracker.save_analysis(analysis, output_file)

    assert output_file.exists()

    with open(output_file) as f:
        saved_data = json.load(f)

    assert saved_data == analysis


def test_tracker_verbose_mode(flask_app_file):
    """Test tracker in verbose mode."""
    tracker = FlaskTracker(flask_app_file, verbose=True)
    assert tracker.verbose is True


def test_tracker_nonexistent_file():
    """Test tracker with non-existent file."""
    tracker = FlaskTracker(Path("nonexistent.py"))
    assert tracker.app is not None
    assert tracker.app.name == "flasktrack"


def test_start_tracking_without_app():
    """Test start tracking without loaded app."""
    tracker = FlaskTracker(Path("nonexistent.py"))
    tracker.app = None

    with pytest.raises(RuntimeError, match="No Flask application loaded"):
        tracker.start_tracking()
