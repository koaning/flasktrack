"""Core tracking functionality for Flask applications."""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        self.app: Optional[Flask] = None
        self._load_app()
    
    def _load_app(self) -> None:
        """Load the Flask application from the given path."""
        if self.app_path.suffix == ".py":
            spec = importlib.util.spec_from_file_location("flask_app", self.app_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules["flask_app"] = module
                spec.loader.exec_module(module)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, Flask):
                        self.app = attr
                        break
                    elif callable(attr) and attr_name in ["create_app", "make_app"]:
                        try:
                            potential_app = attr()
                            if isinstance(potential_app, Flask):
                                self.app = potential_app
                                break
                        except Exception:
                            pass
        
        if not self.app:
            self.app = Flask(__name__)
    
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
                print(f"Request started")
        
        @self.app.after_request
        def after_request(response):
            if self.verbose:
                print(f"Request completed with status {response.status_code}")
            return response
        
        print(f"Tracking Flask app on {host}:{port}")
        print("Note: This is a tracking wrapper, not running the actual app")
    
    def analyze(self) -> Dict[str, Any]:
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
    
    def get_routes(self) -> List[Dict[str, Any]]:
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
    
    def save_analysis(self, analysis: Dict[str, Any], output_path: Path) -> None:
        """Save analysis results to a file.
        
        Args:
            analysis: Analysis results dictionary
            output_path: Path to save the results
        """
        with open(output_path, "w") as f:
            json.dump(analysis, f, indent=2)
            f.write("\n")