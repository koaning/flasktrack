"""Core tracking functionality for Flask applications."""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from flask import Flask


class FlaskTracker:
    """Track and analyze Flask applications."""

    def __init__(self, app_path: Path, verbose: bool = False):
        """Initialize the Flask tracker.
        
        Args:
            app_path: Path to the Flask application file or module
            verbose: Enable verbose output
        """
        self.app_path = app_path
        self.verbose = verbose
        self.app: Flask | None = None
        self._load_app()

    def _load_app(self) -> None:
        """Load the Flask application from the given path."""
        if self.app_path.suffix == ".py" and self.app_path.exists():
            # Add the app's parent directory to sys.path for relative imports
            app_dir = str(self.app_path.parent.absolute())
            path_added = False
            
            try:
                if app_dir not in sys.path:
                    sys.path.insert(0, app_dir)
                    path_added = True
                
                spec = importlib.util.spec_from_file_location("flask_app", self.app_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules["flask_app"] = module
                    spec.loader.exec_module(module)

                    # First, look for Flask app instances
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, Flask):
                            self.app = attr
                            if self.verbose:
                                print(f"Found Flask app instance: {attr_name}")
                            break
                    
                    # If no Flask instance found, look for factory functions
                    if not self.app:
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if callable(attr) and attr_name in ["create_app", "make_app"]:
                                try:
                                    potential_app = attr()
                                    if isinstance(potential_app, Flask):
                                        self.app = potential_app
                                        if self.verbose:
                                            print(f"Created Flask app from factory: {attr_name}")
                                        break
                                except Exception as e:
                                    if self.verbose:
                                        print(f"Failed to create app from {attr_name}: {e}")
                                    pass
            except Exception as e:
                if self.verbose:
                    print(f"Error loading Flask app from {self.app_path}: {e}")
            finally:
                # Clean up sys.path
                if path_added and app_dir in sys.path:
                    sys.path.remove(app_dir)

        if not self.app:
            self.app = Flask("flasktrack")

    def start_tracking(self, host: str = "127.0.0.1", port: int = 5000) -> None:
        """Start tracking the Flask application.
        
        Args:
            host: Host to run the Flask app on
            port: Port to run the Flask app on
        """
        if not self.app:
            raise RuntimeError("No Flask application loaded")

        @self.app.before_request
        def before_request():
            if self.verbose:
                print("Request started")

        @self.app.after_request
        def after_request(response):
            if self.verbose:
                print(f"Request completed with status {response.status_code}")
            return response

        print(f"Tracking Flask app on {host}:{port}")
        print("Note: This is a tracking wrapper, not running the actual app")

    def analyze(self) -> dict[str, Any]:
        """Analyze the Flask application structure.
        
        Returns:
            Dictionary containing analysis results
        """
        if not self.app:
            return {"error": "No Flask application loaded"}

        routes = self.get_routes()

        return {
            "total_routes": len(routes),
            "app_name": self.app.name,
            "debug_mode": self.app.debug,
            "testing_mode": self.app.testing,
            "total_blueprints": len(self.app.blueprints),
            "config_keys": len(self.app.config),
        }

    def get_routes(self) -> list[dict[str, Any]]:
        """Get all routes in the Flask application.
        
        Returns:
            List of route dictionaries
        """
        if not self.app:
            return []

        routes = []
        for rule in self.app.url_map.iter_rules():
            routes.append({
                "rule": rule.rule,
                "endpoint": rule.endpoint,
                "methods": list(rule.methods - {"HEAD", "OPTIONS"}),
            })

        return sorted(routes, key=lambda x: x["rule"])

    def save_analysis(self, analysis: dict[str, Any], output_path: Path) -> None:
        """Save analysis results to a file.
        
        Args:
            analysis: Analysis results dictionary
            output_path: Path to save the results
        """
        with open(output_path, "w") as f:
            json.dump(analysis, f, indent=2)
            f.write("\n")
