"""Model discovery and registration for admin interface."""

import importlib
import inspect
from pathlib import Path

from sqlalchemy import inspect as sqla_inspect

from app import db


class ModelRegistry:
    """Registry for discovering and managing models in the admin interface."""

    def __init__(self):
        self.models = {}
        self._discovered = False

    def discover_models(self):
        """Automatically discover all SQLAlchemy models in the app."""
        if self._discovered:
            return self.models

        models_dir = Path(__file__).parent.parent / "models"

        if not models_dir.exists():
            return self.models

        for model_file in models_dir.glob("*.py"):
            if model_file.name.startswith("_"):
                continue

            module_name = f"app.models.{model_file.stem}"

            try:
                module = importlib.import_module(module_name)

                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, db.Model)
                        and obj != db.Model
                        and hasattr(obj, "__tablename__")
                    ):
                        model_name = name.lower()
                        self.models[model_name] = {
                            "class": obj,
                            "name": name,
                            "tablename": obj.__tablename__,
                            "module": module_name,
                        }

            except ImportError:
                continue

        self._discovered = True
        return self.models

    def get_model(self, model_name):
        """Get a model class by name."""
        if not self._discovered:
            self.discover_models()

        model_info = self.models.get(model_name.lower())
        if model_info:
            return model_info["class"]
        return None

    def get_model_info(self, model_name):
        """Get full model information by name."""
        if not self._discovered:
            self.discover_models()

        return self.models.get(model_name.lower())

    def get_all_models(self):
        """Get all discovered models."""
        if not self._discovered:
            self.discover_models()

        return self.models

    def get_model_columns(self, model):
        """Get column information for a model."""
        mapper = sqla_inspect(model)
        columns = []

        for column in mapper.columns:
            col_info = {
                "name": column.name,
                "type": column.type.__class__.__name__,
                "nullable": column.nullable,
                "unique": column.unique or False,
                "primary_key": column.primary_key,
                "foreign_keys": list(column.foreign_keys)
                if column.foreign_keys
                else [],
            }
            columns.append(col_info)

        return columns


# Global registry instance
model_registry = ModelRegistry()
