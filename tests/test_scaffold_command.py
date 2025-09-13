"""Tests for the scaffold command."""

import pytest
from typer.testing import CliRunner

from flasktrack.cli import app
from flasktrack.scaffold import Scaffold


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def flask_app_dir(tmp_path):
    """Create a minimal Flask app structure for testing."""
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    # Create minimal __init__.py
    init_content = '''"""Flask application factory."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_name="development"):
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="views")

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.controllers.auth import auth_bp
    from app.controllers.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    @app.shell_context_processor
    def make_shell_context():
        """Make database models available in flask shell."""
        from app.models.user import User

        return {"db": db, "User": User}

    return app
'''
    (app_dir / "__init__.py").write_text(init_content)

    # Create necessary subdirectories
    (app_dir / "models").mkdir()
    (app_dir / "controllers").mkdir()
    (app_dir / "forms").mkdir()
    (app_dir / "views").mkdir()

    # Create __init__ files for packages
    (app_dir / "models" / "__init__.py").touch()
    (app_dir / "controllers" / "__init__.py").touch()
    (app_dir / "forms" / "__init__.py").touch()

    return tmp_path


class TestScaffoldClass:
    """Test the Scaffold class directly."""

    def test_parse_fields_basic_types(self):
        """Test parsing basic field types."""
        scaffold = Scaffold(
            "Post", ["title:string", "content:text", "published:boolean"]
        )

        assert len(scaffold.fields) == 3
        assert scaffold.fields[0]["name"] == "title"
        assert scaffold.fields[0]["type"] == "string"
        assert scaffold.fields[0]["sqlalchemy_type"] == "db.String(255)"

        assert scaffold.fields[1]["name"] == "content"
        assert scaffold.fields[1]["type"] == "text"
        assert scaffold.fields[1]["sqlalchemy_type"] == "db.Text"

        assert scaffold.fields[2]["name"] == "published"
        assert scaffold.fields[2]["type"] == "boolean"
        assert scaffold.fields[2]["sqlalchemy_type"] == "db.Boolean"

    def test_parse_fields_references(self):
        """Test parsing reference fields."""
        scaffold = Scaffold(
            "Comment", ["body:text", "post:references", "user:belongs_to"]
        )

        assert scaffold.fields[1]["name"] == "post"
        assert scaffold.fields[1]["type"] == "references"
        assert scaffold.fields[1]["is_reference"] is True
        assert scaffold.fields[1]["referenced_model"] == "Post"

        assert scaffold.fields[2]["name"] == "user"
        assert scaffold.fields[2]["type"] == "belongs_to"
        assert scaffold.fields[2]["is_reference"] is True
        assert scaffold.fields[2]["referenced_model"] == "User"

    def test_parse_fields_invalid_type(self):
        """Test that invalid field types raise an error."""
        with pytest.raises(ValueError, match="Invalid field type"):
            Scaffold("Post", ["title:invalid_type"])

    def test_parse_fields_invalid_format(self):
        """Test that invalid field format raises an error."""
        with pytest.raises(ValueError, match="Invalid field definition"):
            Scaffold("Post", ["title"])

    def test_pluralization(self):
        """Test model name pluralization."""
        tests = [
            ("post", "posts"),
            ("category", "categories"),
            ("person", "people"),
            ("child", "children"),
            ("box", "boxes"),
            ("class", "classes"),
            ("dish", "dishes"),
            ("church", "churches"),
            ("knife", "knives"),
            ("life", "lives"),
        ]

        for singular, expected_plural in tests:
            scaffold = Scaffold(singular.capitalize(), [])
            assert scaffold.name_plural == expected_plural

    def test_generate_model(self):
        """Test model generation."""
        scaffold = Scaffold(
            "Post", ["title:string", "content:text", "author:references"]
        )
        model_code = scaffold.generate_model()

        # Check for class definition
        assert "class Post(db.Model):" in model_code
        assert '__tablename__ = "posts"' in model_code

        # Check for fields
        assert "title = db.Column(db.String(255), nullable=False)" in model_code
        assert "content = db.Column(db.Text, nullable=False)" in model_code
        assert (
            "author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)"
            in model_code
        )

        # Check for relationships
        assert "author = db.relationship('Author')" in model_code

        # Check for TODO comments
        assert "# TODO: Add these relationships to the referenced models:" in model_code
        assert "# In Author model:" in model_code

    def test_generate_controller(self):
        """Test controller generation."""
        scaffold = Scaffold("Post", ["title:string", "content:text"])
        controller_code = scaffold.generate_controller()

        # Check for blueprint
        assert 'posts_bp = Blueprint("posts", __name__)' in controller_code

        # Check for CRUD routes
        assert '@posts_bp.route("/")' in controller_code
        assert "def index():" in controller_code
        assert '@posts_bp.route("/<int:id>")' in controller_code
        assert "def show(id):" in controller_code
        assert '@posts_bp.route("/new", methods=["GET", "POST"])' in controller_code
        assert "def new():" in controller_code
        assert (
            '@posts_bp.route("/<int:id>/edit", methods=["GET", "POST"])'
            in controller_code
        )
        assert "def edit(id):" in controller_code
        assert (
            '@posts_bp.route("/<int:id>/delete", methods=["POST"])' in controller_code
        )
        assert "def delete(id):" in controller_code

        # Check for login_required decorators
        assert "@login_required" in controller_code

    def test_generate_form(self):
        """Test form generation."""
        scaffold = Scaffold(
            "Post", ["title:string", "content:text", "published:boolean"]
        )
        form_code = scaffold.generate_form()

        # Check for form class
        assert "class PostForm(FlaskForm):" in form_code

        # Check for fields
        assert (
            'title = StringField("Title", validators=[DataRequired(), Length(max=255)])'
            in form_code
        )
        assert (
            'content = TextAreaField("Content", validators=[DataRequired()])'
            in form_code
        )
        assert 'published = BooleanField("Published")' in form_code
        assert 'submit = SubmitField("Save")' in form_code

    def test_generate_form_with_references(self):
        """Test form generation with reference fields."""
        scaffold = Scaffold("Comment", ["body:text", "post:references"])
        form_code = scaffold.generate_form()

        # Check for SelectField
        assert (
            'post_id = SelectField("Post", coerce=int, validators=[DataRequired()])'
            in form_code
        )

        # Check for __init__ method to populate choices
        assert "def __init__(self, *args, **kwargs):" in form_code
        assert "self.post_id.choices = [" in form_code


class TestScaffoldCommand:
    """Test the scaffold CLI command."""

    def test_scaffold_creates_all_files(self, runner, flask_app_dir, monkeypatch):
        """Test that scaffold creates all expected files."""
        monkeypatch.chdir(flask_app_dir)

        result = runner.invoke(
            app, ["scaffold", "Post", "title:string", "content:text"]
        )

        assert result.exit_code == 0
        assert "Creating scaffold for Post" in result.output
        assert "Created app/models/post.py" in result.output
        assert "Created app/controllers/posts.py" in result.output
        assert "Created app/forms/post.py" in result.output
        assert "Created app/views/posts/index.html" in result.output
        assert "Created app/views/posts/show.html" in result.output
        assert "Created app/views/posts/new.html" in result.output
        assert "Created app/views/posts/edit.html" in result.output
        assert "Created app/views/posts/_form.html" in result.output

        # Check files exist
        assert (flask_app_dir / "app/models/post.py").exists()
        assert (flask_app_dir / "app/controllers/posts.py").exists()
        assert (flask_app_dir / "app/forms/post.py").exists()
        assert (flask_app_dir / "app/views/posts/index.html").exists()

    def test_scaffold_with_references(self, runner, flask_app_dir, monkeypatch):
        """Test scaffold with reference fields."""
        monkeypatch.chdir(flask_app_dir)

        result = runner.invoke(
            app, ["scaffold", "Comment", "body:text", "post:references"]
        )

        assert result.exit_code == 0
        assert "Add relationships to referenced models" in result.output

        # Check model file for references
        model_content = (flask_app_dir / "app/models/comment.py").read_text()
        assert "post_id = db.Column(db.Integer, db.ForeignKey" in model_content
        assert "post = db.relationship('Post')" in model_content

    def test_scaffold_updates_app_init(self, runner, flask_app_dir, monkeypatch):
        """Test that scaffold updates app/__init__.py."""
        monkeypatch.chdir(flask_app_dir)

        result = runner.invoke(app, ["scaffold", "Post", "title:string"])

        assert result.exit_code == 0
        assert "Updated app/__init__.py" in result.output

        # Check that __init__.py was updated
        init_content = (flask_app_dir / "app/__init__.py").read_text()
        assert "from app.controllers.posts import posts_bp" in init_content
        assert "app.register_blueprint(posts_bp" in init_content

    def test_scaffold_skip_init_option(self, runner, flask_app_dir, monkeypatch):
        """Test scaffold with --skip-init option."""
        monkeypatch.chdir(flask_app_dir)

        result = runner.invoke(app, ["scaffold", "Post", "title:string", "--skip-init"])

        assert result.exit_code == 0
        assert "Updated app/__init__.py" not in result.output

        # Check that __init__.py was NOT updated
        init_content = (flask_app_dir / "app/__init__.py").read_text()
        assert "from app.controllers.posts import posts_bp" not in init_content

    def test_scaffold_existing_model_error(self, runner, flask_app_dir, monkeypatch):
        """Test that scaffold fails if model already exists."""
        monkeypatch.chdir(flask_app_dir)

        # Create existing model file
        (flask_app_dir / "app/models/post.py").touch()

        result = runner.invoke(app, ["scaffold", "Post", "title:string"])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_scaffold_not_in_flask_app(self, runner, tmp_path, monkeypatch):
        """Test that scaffold fails when not in a Flask app directory."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["scaffold", "Post", "title:string"])

        assert result.exit_code == 1
        assert "No 'app' directory found" in result.output

    def test_scaffold_invalid_field_type(self, runner, flask_app_dir, monkeypatch):
        """Test that scaffold fails with invalid field type."""
        monkeypatch.chdir(flask_app_dir)

        result = runner.invoke(app, ["scaffold", "Post", "title:invalid_type"])

        assert result.exit_code == 1
        assert "Invalid field type" in result.output

    def test_scaffold_all_field_types(self, runner, flask_app_dir, monkeypatch):
        """Test scaffold with all supported field types."""
        monkeypatch.chdir(flask_app_dir)

        fields = [
            "name:string",
            "description:text",
            "age:integer",
            "price:float",
            "cost:decimal",
            "active:boolean",
            "birth_date:date",
            "created:datetime",
            "user:references",
        ]

        result = runner.invoke(app, ["scaffold", "Product"] + fields)

        assert result.exit_code == 0

        # Check model file for all types
        model_content = (flask_app_dir / "app/models/product.py").read_text()
        assert "name = db.Column(db.String(255)" in model_content
        assert "description = db.Column(db.Text" in model_content
        assert "age = db.Column(db.Integer" in model_content
        assert "price = db.Column(db.Float" in model_content
        assert "cost = db.Column(db.Numeric" in model_content
        assert "active = db.Column(db.Boolean" in model_content
        assert "birth_date = db.Column(db.Date" in model_content
        assert "created = db.Column(db.DateTime" in model_content
        assert "user_id = db.Column(db.Integer, db.ForeignKey" in model_content
