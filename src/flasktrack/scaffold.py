"""Scaffold generator for FlaskTrack."""

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class Scaffold:
    """Generate scaffold files for a Flask model."""

    # Type mappings from scaffold types to SQLAlchemy types
    TYPE_MAPPINGS = {
        "string": "db.String(255)",
        "text": "db.Text",
        "integer": "db.Integer",
        "float": "db.Float",
        "decimal": "db.Numeric",
        "boolean": "db.Boolean",
        "date": "db.Date",
        "datetime": "db.DateTime",
        "references": "reference",  # Special handling
        "belongs_to": "reference",  # Alias for references
    }

    # Form field mappings
    FORM_FIELD_MAPPINGS = {
        "string": "StringField",
        "text": "TextAreaField",
        "integer": "IntegerField",
        "float": "FloatField",
        "decimal": "DecimalField",
        "boolean": "BooleanField",
        "date": "DateField",
        "datetime": "DateTimeField",
        "references": "SelectField",
        "belongs_to": "SelectField",
    }

    def __init__(self, name: str, fields: list[str]):
        """Initialize scaffold generator.

        Args:
            name: Model name (e.g., 'Post')
            fields: List of field definitions (e.g., ['title:string', 'user:references'])
        """
        self.name = name
        self.name_lower = name.lower()
        self.name_plural = self.pluralize(self.name_lower)
        self.fields = self.parse_fields(fields)

        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / "templates" / "scaffold"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def parse_fields(self, field_definitions: list[str]) -> list[dict[str, Any]]:
        """Parse field definitions into structured format.

        Args:
            field_definitions: List of 'name:type' strings

        Returns:
            List of field dictionaries with name, type, and metadata
        """
        fields = []
        for field_def in field_definitions:
            if ":" not in field_def:
                raise ValueError(
                    f"Invalid field definition: {field_def}. Use format 'name:type'"
                )

            name, field_type = field_def.split(":", 1)

            # Check for custom model in references (e.g., author:references[User])
            referenced_model = None
            if field_type.startswith(("references", "belongs_to")):
                match = re.match(r"(references|belongs_to)(?:\[(\w+)\])?", field_type)
                if match:
                    field_type = match.group(1)
                    referenced_model = match.group(2)
                    if not referenced_model:
                        # Infer model from field name (e.g., 'user' -> 'User')
                        referenced_model = name.capitalize()

            if field_type not in self.TYPE_MAPPINGS:
                raise ValueError(
                    f"Invalid field type: {field_type}. "
                    f"Valid types: {', '.join(self.TYPE_MAPPINGS.keys())}"
                )

            field_info = {
                "name": name,
                "type": field_type,
                "sqlalchemy_type": self.TYPE_MAPPINGS[field_type],
                "form_field_type": self.FORM_FIELD_MAPPINGS[field_type],
                "is_reference": field_type in ("references", "belongs_to"),
                "referenced_model": referenced_model,
            }

            fields.append(field_info)

        return fields

    def pluralize(self, word: str) -> str:
        """Simple pluralization of model names.

        Args:
            word: Singular word to pluralize

        Returns:
            Pluralized word
        """
        # Common irregular plurals
        irregular = {
            "person": "people",
            "child": "children",
            "man": "men",
            "woman": "women",
            "tooth": "teeth",
            "foot": "feet",
            "mouse": "mice",
            "goose": "geese",
        }

        if word in irregular:
            return irregular[word]

        # Rules for regular plurals
        if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            return word[:-1] + "ies"
        elif word.endswith(("s", "ss", "sh", "ch", "x", "z", "o")):
            return word + "es"
        elif word.endswith("f"):
            return word[:-1] + "ves"
        elif word.endswith("fe"):
            return word[:-2] + "ves"
        else:
            return word + "s"

    def generate_model(self) -> str:
        """Generate model code."""
        template = self.env.get_template("model.py.jinja2")

        # Collect referenced models for TODO comments
        referenced_models = [field for field in self.fields if field["is_reference"]]

        return template.render(
            model_name=self.name,
            table_name=self.name_plural,
            fields=self.fields,
            referenced_models=referenced_models,
        )

    def generate_controller(self) -> str:
        """Generate controller/blueprint code."""
        template = self.env.get_template("controller.py.jinja2")

        return template.render(
            model_name=self.name,
            model_name_lower=self.name_lower,
            model_name_plural=self.name_plural,
            fields=self.fields,
            has_references=any(f["is_reference"] for f in self.fields),
        )

    def generate_form(self) -> str:
        """Generate form code."""
        template = self.env.get_template("form.py.jinja2")

        return template.render(
            model_name=self.name,
            fields=self.fields,
            has_references=any(f["is_reference"] for f in self.fields),
        )

    def generate_views(self) -> dict[str, str]:
        """Generate all view templates.

        Returns:
            Dictionary mapping template names to content
        """
        views = {}

        # Template names to generate
        template_names = [
            "index.html",
            "show.html",
            "new.html",
            "edit.html",
            "_form.html",
        ]

        for template_name in template_names:
            template = self.env.get_template(f"{template_name}.jinja2")
            views[template_name] = template.render(
                model_name=self.name,
                model_name_lower=self.name_lower,
                model_name_plural=self.name_plural,
                fields=self.fields,
            )

        return views

    def write_files(self, base_path: Path) -> list[Path]:
        """Write all scaffold files to disk.

        Args:
            base_path: Base directory of the Flask app

        Returns:
            List of created file paths
        """
        created_files = []

        # Ensure base directories exist
        app_dir = base_path / "app"
        models_dir = app_dir / "models"
        controllers_dir = app_dir / "controllers"
        forms_dir = app_dir / "forms"
        views_dir = app_dir / "views" / self.name_plural

        for directory in [models_dir, controllers_dir, forms_dir, views_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Write model
        model_path = models_dir / f"{self.name_lower}.py"
        if model_path.exists():
            raise FileExistsError(f"Model already exists: {model_path}")
        model_path.write_text(self.generate_model())
        created_files.append(model_path)

        # Write controller
        controller_path = controllers_dir / f"{self.name_plural}.py"
        if controller_path.exists():
            raise FileExistsError(f"Controller already exists: {controller_path}")
        controller_path.write_text(self.generate_controller())
        created_files.append(controller_path)

        # Write form
        form_path = forms_dir / f"{self.name_lower}.py"
        if form_path.exists():
            raise FileExistsError(f"Form already exists: {form_path}")
        form_path.write_text(self.generate_form())
        created_files.append(form_path)

        # Write views
        views = self.generate_views()
        for view_name, view_content in views.items():
            view_path = views_dir / view_name
            view_path.write_text(view_content)
            created_files.append(view_path)

        return created_files

    def update_app_init(self, app_init_path: Path) -> bool:
        """Update app/__init__.py to register the new blueprint.

        Args:
            app_init_path: Path to app/__init__.py

        Returns:
            True if updated successfully
        """
        if not app_init_path.exists():
            return False

        content = app_init_path.read_text()

        # Check if blueprint is already imported
        import_line = (
            f"from app.controllers.{self.name_plural} import {self.name_plural}_bp"
        )
        if import_line in content:
            return False  # Already registered

        # Find the blueprint import section
        import_pattern = re.compile(
            r"(\s+# Register blueprints\n)(.*?)(from app\.controllers\.\w+ import \w+_bp\n)"
        )
        match = import_pattern.search(content)

        if match:
            # Add import after the last blueprint import
            last_import_end = match.end()
            content = (
                content[:last_import_end]
                + f"    {import_line}\n"
                + content[last_import_end:]
            )
        else:
            # If no blueprint imports found, add before the app.register_blueprint calls
            register_pattern = re.compile(r"(\s+)(app\.register_blueprint\()")
            match = register_pattern.search(content)
            if match:
                indent = match.group(1)
                insert_pos = match.start()
                content = (
                    content[:insert_pos]
                    + f"{indent}{import_line}\n\n"
                    + content[insert_pos:]
                )

        # Add blueprint registration
        register_line = f"app.register_blueprint({self.name_plural}_bp, url_prefix='/{self.name_plural}')"
        if register_line not in content:
            # Find the last register_blueprint call
            register_pattern = re.compile(r"(app\.register_blueprint\([^)]+\))")
            matches = list(register_pattern.finditer(content))
            if matches:
                last_match = matches[-1]
                insert_pos = last_match.end()
                # Get the indentation from the last match
                line_start = content.rfind("\n", 0, last_match.start()) + 1
                indent = content[line_start : last_match.start()]
                content = (
                    content[:insert_pos]
                    + f"\n{indent}{register_line}"
                    + content[insert_pos:]
                )

        # Update shell context processor to include the new model
        shell_context_pattern = re.compile(
            r"(@app\.shell_context_processor\s+def make_shell_context\(\):.*?)(from app\.models\.\w+ import \w+\n)",
            re.DOTALL,
        )
        match = shell_context_pattern.search(content)

        if match:
            model_import = f"from app.models.{self.name_lower} import {self.name}"
            if model_import not in content:
                # Add model import
                insert_pos = match.end()
                indent = "        "  # Standard indent for imports in shell context
                content = (
                    content[:insert_pos]
                    + f"{indent}{model_import}\n"
                    + content[insert_pos:]
                )

                # Add to return dictionary
                return_pattern = re.compile(r'(return \{[^}]+)"User": User')
                return_match = return_pattern.search(content)
                if return_match:
                    insert_pos = return_match.end()
                    content = (
                        content[:insert_pos]
                        + f', "{self.name}": {self.name}'
                        + content[insert_pos:]
                    )

        app_init_path.write_text(content)
        return True
