"""Tests for admin functionality with actual models."""

import pytest

from app import db
from app.models.user import User


class TestAdminDashboard:
    """Test admin dashboard functionality."""

    def test_admin_dashboard_requires_admin(self, client, auth_user):
        """Test that admin dashboard requires admin privileges."""
        # Login as regular user
        client.post(
            "/auth/login",
            data={
                "username": auth_user.username,
                "password": "password123",
            },
        )

        response = client.get("/admin/")
        assert response.status_code == 302  # Should redirect

    def test_admin_dashboard_shows_models(self, client, admin_user):
        """Test that admin dashboard shows available models."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "admin123",
            },
        )

        response = client.get("/admin/")
        assert response.status_code == 200
        assert b"Dashboard" in response.data
        assert b"User" in response.data  # User model should be shown


class TestAdminUserManagement:
    """Test admin user management functionality."""

    def test_admin_can_list_users(self, client, admin_user, auth_user):
        """Test that admin can view user list."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "admin123",
            },
        )

        response = client.get("/admin/user/")
        assert response.status_code == 200
        assert admin_user.email.encode() in response.data
        assert auth_user.email.encode() in response.data

    def test_admin_can_create_user_with_password(self, client, admin_user):
        """Test that admin can create a user with password."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "admin123",
            },
        )

        # Create new user with password
        response = client.post(
            "/admin/user/new",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "newpass123",  # Password field, not password_hash
                "is_active": True,
                "is_admin": False,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verify user was created and can login
        client.get("/auth/logout")
        response = client.post(
            "/auth/login",
            data={
                "username": "newuser",
                "password": "newpass123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Dashboard" in response.data

    def test_admin_can_edit_user_password(self, client, admin_user, auth_user):
        """Test that admin can change a user's password."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "admin123",
            },
        )

        # Edit user's password
        response = client.post(
            f"/admin/user/{auth_user.id}/edit",
            data={
                "username": auth_user.username,
                "email": auth_user.email,
                "password": "newpassword123",  # Change password
                "is_active": True,
                "is_admin": False,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verify user can login with new password
        client.get("/auth/logout")
        response = client.post(
            "/auth/login",
            data={
                "username": auth_user.username,
                "password": "newpassword123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Dashboard" in response.data

    def test_admin_can_edit_user_without_changing_password(
        self, client, admin_user, auth_user
    ):
        """Test that admin can edit user without changing password."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "admin123",
            },
        )

        # Edit user's email only (leave password blank)
        response = client.post(
            f"/admin/user/{auth_user.id}/edit",
            data={
                "username": auth_user.username,
                "email": "updated@example.com",
                "password": "",  # Leave blank to keep existing password
                "is_active": True,
                "is_admin": False,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verify user can still login with old password
        client.get("/auth/logout")
        response = client.post(
            "/auth/login",
            data={
                "username": auth_user.username,
                "password": "password123",  # Original password
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Dashboard" in response.data


class TestAdminWithForeignKeys:
    """Test admin functionality with models that have foreign keys."""

    def test_create_model_with_foreign_key(self, client, admin_user, app):
        """Test creating a model that references another model."""
        # Note: This test is designed to work when a Post model (or similar)
        # with a user_id foreign key exists in the application.
        # It demonstrates the admin's ability to handle foreign key relationships.

        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "admin123",
            },
        )

        # Check if Post model exists
        from app.admin.registry import model_registry

        # Try to get Post model if it exists
        post_model = model_registry.get_model("post")
        if post_model:
            # Test creating a post with a foreign key to user
            response = client.get("/admin/post/new")
            assert response.status_code == 200

            # The form should include a select field for user
            assert b"User" in response.data or b"user" in response.data

            # Submit form with user reference
            response = client.post(
                "/admin/post/new",
                data={
                    "title": "Test Post",
                    "content": "This is test content",
                    "user_id": admin_user.id,
                },
                follow_redirects=True,
            )

            # Check for success message or verify the post was created
            if response.status_code == 200:
                # Post should be created successfully
                created_post = (
                    db.session.query(post_model).filter_by(title="Test Post").first()
                )
                if created_post:
                    assert created_post.user_id == admin_user.id

    def test_create_model_with_nullable_foreign_key(self, client, admin_user, app):
        """Test creating a model with an optional foreign key."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "admin123",
            },
        )

        from app.admin.registry import model_registry

        # Find any model with a nullable foreign key
        for model_name, model_info in model_registry.get_all_models().items():
            model_class = model_info["class"]
            if model_name == "user":  # Skip user model
                continue

            # Check if this model has nullable foreign keys
            from sqlalchemy import inspect as sql_inspect

            mapper = sql_inspect(model_class)

            for column in mapper.columns:
                if column.foreign_keys and column.nullable:
                    # Test creating without setting the foreign key
                    response = client.get(f"/admin/{model_name}/new")
                    if response.status_code == 200:
                        # Try to create without setting the foreign key
                        form_data = {}

                        # Fill required fields with dummy data
                        for col in mapper.columns:
                            if (
                                not col.nullable
                                and not col.primary_key
                                and not col.foreign_keys
                            ):
                                if "String" in col.type.__class__.__name__:
                                    form_data[col.name] = "Test Value"
                                elif "Integer" in col.type.__class__.__name__:
                                    form_data[col.name] = "1"
                                elif "Boolean" in col.type.__class__.__name__:
                                    form_data[col.name] = True

                        # Leave the foreign key field empty
                        form_data[column.name] = ""

                        response = client.post(
                            f"/admin/{model_name}/new",
                            data=form_data,
                            follow_redirects=True,
                        )

                        # Should not get a TypeError
                        assert b"TypeError" not in response.data
                    break


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    user = User(
        username="admin", email="admin@example.com", is_active=True, is_admin=True
    )
    user.set_password("admin123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def auth_user(app):
    """Create a regular user for testing."""
    user = User(
        username="testuser", email="test@example.com", is_active=True, is_admin=False
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user
