"""Test admin functionality with scaffolded models."""

import os
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from flasktrack.cli import app as cli_app


class TestAdminWithScaffoldedModels:
    """Test admin interface with models created via scaffold command."""

    def test_admin_create_post_with_foreign_key(self):
        """Test creating a Post model with user foreign key through admin."""
        runner = CliRunner()

        # Save the original working directory
        original_cwd = os.getcwd()

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)

                # Initialize a Flask app
                result = runner.invoke(cli_app, ["init", "testapp"])
                assert result.exit_code == 0

                # Change to the app directory
                app_dir = Path(tmpdir) / "testapp"
                os.chdir(app_dir)

                # Create an admin user
                result = runner.invoke(
                    cli_app,
                    [
                        "add-admin",
                        "admin",
                        "admin@test.com",
                        "--password",
                        "admin123",
                        "--app-path",
                        str(app_dir),
                    ],
                )
                if result.exit_code != 0:
                    print(f"add-admin failed: {result.output}")
                    print(f"Exception: {result.exception}")
                assert result.exit_code == 0

                # Scaffold a Post model with user reference
                result = runner.invoke(
                    cli_app,
                    [
                        "scaffold",
                        "Post",
                        "title:string",
                        "content:text",
                        "user:references",
                    ],
                )
                assert result.exit_code == 0
                assert "Scaffold created successfully" in result.output

                # Now test the admin interface
                # Import the app and test client
                import sys

                sys.path.insert(0, str(app_dir))

                from app import create_app, db
                from app.models.post import Post
                from app.models.user import User

                app = create_app()
                app.config["TESTING"] = True
                app.config["WTF_CSRF_ENABLED"] = False

                with app.app_context():
                    db.create_all()

                    # Get the admin user
                    admin_user = User.query.filter_by(username="admin").first()
                    assert admin_user is not None

                    with app.test_client() as client:
                        # Login as admin
                        response = client.post(
                            "/auth/login",
                            data={
                                "username": "admin",
                                "password": "admin123",
                            },
                        )
                        assert response.status_code == 302

                        # Go to admin dashboard
                        response = client.get("/admin/")
                        assert response.status_code == 200
                        assert b"Post" in response.data

                        # Go to create new post
                        response = client.get("/admin/post/new")
                        assert response.status_code == 200

                        # Check that the form renders without TypeError
                        assert b"TypeError" not in response.data
                        assert b"Title" in response.data
                        assert b"Content" in response.data
                        assert b"User" in response.data

                        # Create a new post with user reference
                        response = client.post(
                            "/admin/post/new",
                            data={
                                "title": "Test Post",
                                "content": "This is test content",
                                "user_id": str(admin_user.id),
                            },
                            follow_redirects=True,
                        )

                        # Check response
                        assert response.status_code == 200
                        assert b"TypeError" not in response.data

                        # Verify post was created
                        post = Post.query.filter_by(title="Test Post").first()
                        assert post is not None
                        assert post.user_id == admin_user.id
                        assert post.content == "This is test content"

                        # Test creating post without user (if nullable)
                        response = client.post(
                            "/admin/post/new",
                            data={
                                "title": "Another Post",
                                "content": "More content",
                                "user_id": "",  # Empty foreign key
                            },
                            follow_redirects=True,
                        )

                        # Should handle empty foreign key gracefully
                        assert b"TypeError" not in response.data
        finally:
            # Restore the original working directory
            os.chdir(original_cwd)
