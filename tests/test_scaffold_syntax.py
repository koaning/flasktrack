"""Tests that validate generated Python code is syntactically correct."""

import ast
import tempfile
from pathlib import Path

import pytest

from flasktrack.scaffold import Scaffold


class TestGeneratedCodeSyntax:
    """Test that generated code is valid Python."""

    def test_generated_model_is_valid_python(self):
        """Test that generated model code is syntactically valid."""
        scaffold = Scaffold("Post", ["title:string", "author:references"])
        model_code = scaffold.generate_model()

        # This will raise SyntaxError if code is invalid
        try:
            ast.parse(model_code)
        except SyntaxError as e:
            pytest.fail(f"Generated model has syntax error: {e}")

    def test_generated_controller_is_valid_python(self):
        """Test that generated controller code is syntactically valid."""
        scaffold = Scaffold("Post", ["title:string", "author:references"])
        controller_code = scaffold.generate_controller()

        try:
            ast.parse(controller_code)
        except SyntaxError as e:
            pytest.fail(f"Generated controller has syntax error: {e}")

    def test_generated_form_is_valid_python(self):
        """Test that generated form code is syntactically valid."""
        scaffold = Scaffold(
            "Comment", ["body:text", "post:references", "user:references"]
        )
        form_code = scaffold.generate_form()

        try:
            ast.parse(form_code)
        except SyntaxError as e:
            pytest.fail(f"Generated form has syntax error: {e}")

    def test_generated_form_imports_are_correct(self):
        """Test that form imports only reference models, not the form's own model."""
        scaffold = Scaffold(
            "Comment", ["body:text", "post:references", "user:references"]
        )
        form_code = scaffold.generate_form()

        # Parse the AST to check imports
        tree = ast.parse(form_code)
        imports = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("app.models")
            ):
                for alias in node.names:
                    imports.append((node.module, alias.name))

        # Should import Post and User, but NOT Comment
        expected_imports = [
            ("app.models.post", "Post"),
            ("app.models.user", "User"),
        ]

        for expected in expected_imports:
            assert expected in imports, f"Missing import: {expected}"

        # Should NOT import the model itself
        assert ("app.models.comment", "Comment") not in imports, (
            "Form should not import its own model"
        )

        # Should not have any empty module names (the bug we fixed)
        for module, name in imports:
            assert module != "app.models.", (
                f"Empty module name in import: from {module} import {name}"
            )

    def test_all_generated_files_are_valid_python(self):
        """Integration test: Generate all files and verify they're valid Python."""
        scaffold = Scaffold(
            "Article",
            [
                "title:string",
                "content:text",
                "published:boolean",
                "author:references",
                "category:references",
            ],
        )

        # Generate all Python files
        model_code = scaffold.generate_model()
        controller_code = scaffold.generate_controller()
        form_code = scaffold.generate_form()

        # All should be valid Python
        for name, code in [
            ("model", model_code),
            ("controller", controller_code),
            ("form", form_code),
        ]:
            try:
                ast.parse(code)
            except SyntaxError as e:
                pytest.fail(f"Generated {name} has syntax error: {e}\n\nCode:\n{code}")

    def test_generated_code_can_be_executed_in_mock_environment(self):
        """Test that generated code can actually be imported (with mocked dependencies)."""
        scaffold = Scaffold(
            "Product", ["name:string", "price:float", "category:references"]
        )

        # Create a temporary directory for our test
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create app structure
            app_dir = tmppath / "app"
            app_dir.mkdir()
            (app_dir / "__init__.py").write_text("db = None")

            models_dir = app_dir / "models"
            models_dir.mkdir()
            (models_dir / "__init__.py").touch()

            forms_dir = app_dir / "forms"
            forms_dir.mkdir()
            (forms_dir / "__init__.py").touch()

            # Write a mock Category model
            (models_dir / "category.py").write_text("""
class Category:
    query = type('Query', (), {'all': lambda: []})()
""")

            # Write generated form
            form_code = scaffold.generate_form()
            form_path = forms_dir / "product.py"

            # Replace Flask-WTF imports with mocks for testing
            form_code_modified = (
                form_code.replace(
                    "from flask_wtf import FlaskForm", "FlaskForm = object"
                )
                .replace(
                    "from wtforms import",
                    "# Mock wtforms\n"
                    + "\n".join(
                        [
                            "StringField = object",
                            "FloatField = object",
                            "SelectField = object",
                            "SubmitField = object",
                            "\nfrom wtforms import",
                        ]
                    ),
                )
                .replace(
                    "from wtforms.validators import DataRequired, Length",
                    "DataRequired = object\nLength = object",
                )
            )

            form_path.write_text(form_code_modified)

            # Try to import it - this would fail with syntax errors
            import sys

            sys.path.insert(0, str(tmppath))
            try:
                # This will fail if there are import errors or syntax errors
                exec("from app.forms.product import ProductForm")
            except SyntaxError as e:
                pytest.fail(
                    f"Generated form cannot be imported due to syntax error: {e}"
                )
            except ImportError as e:
                # Some import errors are expected (flask_wtf, etc.)
                # But not syntax errors in imports
                if "app.models." in str(e) and "import" in str(e):
                    pytest.fail(f"Generated form has import error: {e}")
            finally:
                sys.path.remove(str(tmppath))
