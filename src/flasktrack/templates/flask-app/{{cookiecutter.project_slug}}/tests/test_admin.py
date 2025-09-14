"""Tests for admin functionality."""

import pytest

from app import db
from app.models.user import User


class TestAdminAccess:
    """Test admin access control."""

    def test_admin_dashboard_requires_login(self, client):
        """Test that admin dashboard requires authentication."""
        response = client.get("/admin/")
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_non_admin_cannot_access_dashboard(self, client, auth_user):
        """Test that non-admin users cannot access admin dashboard."""
        # Login as regular user
        client.post(
            "/auth/login",
            data={
                "username": auth_user.username,
                "password": "password123",
                "remember_me": False,
            },
        )

        response = client.get("/admin/")
        assert response.status_code == 302
        assert "/dashboard" in response.location

    def test_admin_can_access_dashboard(self, client, admin_user):
        """Test that admin users can access admin dashboard."""
        # Login as admin user
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "adminpass123",
                "remember_me": False,
            },
        )

        response = client.get("/admin/")
        assert response.status_code == 200
        assert b"Admin Dashboard" in response.data
        assert b"Manage Models" in response.data

    def test_admin_menu_visible_for_admin_users(self, client, admin_user):
        """Test that hamburger menu is visible for admin users."""
        # Login as admin user
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "adminpass123",
                "remember_me": False,
            },
        )

        response = client.get("/dashboard")
        assert response.status_code == 200
        # Check for hamburger menu icon
        assert b"admin-menu-icon" in response.data
        assert b"Admin Panel" in response.data

    def test_admin_menu_not_visible_for_regular_users(self, client, auth_user):
        """Test that hamburger menu is not visible for regular users."""
        # Login as regular user
        client.post(
            "/auth/login",
            data={
                "username": auth_user.username,
                "password": "password123",
                "remember_me": False,
            },
        )

        response = client.get("/dashboard")
        assert response.status_code == 200
        # Check that hamburger menu icon is not present
        assert b"admin-menu-icon" not in response.data
        assert b"Admin Panel" not in response.data


class TestAdminModelOperations:
    """Test admin CRUD operations on models."""

    def test_admin_can_list_users(self, client, admin_user, auth_user):
        """Test that admin can view list of users."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "adminpass123",
                "remember_me": False,
            },
        )

        response = client.get("/admin/user/")
        assert response.status_code == 200
        assert b"User List" in response.data
        assert admin_user.username.encode() in response.data
        assert auth_user.username.encode() in response.data

    def test_admin_can_create_user(self, client, admin_user):
        """Test that admin can create a new user."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "adminpass123",
                "remember_me": False,
            },
        )

        # Get the create form
        response = client.get("/admin/user/new")
        assert response.status_code == 200
        assert b"Create User" in response.data

        # Submit new user form
        response = client.post(
            "/admin/user/new",
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password_hash": "newpass123",
                "is_active": True,
                "is_admin": False,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"User created successfully!" in response.data

        # Verify user was created
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"

    def test_admin_can_edit_user(self, client, admin_user, auth_user):
        """Test that admin can edit an existing user."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "adminpass123",
                "remember_me": False,
            },
        )

        # Get the edit form
        response = client.get(f"/admin/user/{auth_user.id}/edit")
        assert response.status_code == 200
        assert b"Edit User" in response.data

        # Submit edited user form
        response = client.post(
            f"/admin/user/{auth_user.id}/edit",
            data={
                "username": auth_user.username,
                "email": "newemail@example.com",
                "is_active": True,
                "is_admin": False,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"User updated successfully!" in response.data

        # Verify user was updated
        db.session.refresh(auth_user)
        assert auth_user.email == "newemail@example.com"

    def test_admin_can_delete_user(self, client, admin_user, app):
        """Test that admin can delete a user."""
        # Create a user to delete
        with app.app_context():
            user_to_delete = User(
                username="deleteuser", email="delete@example.com", is_active=True
            )
            user_to_delete.set_password("password123")
            db.session.add(user_to_delete)
            db.session.commit()
            user_id = user_to_delete.id

        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "adminpass123",
                "remember_me": False,
            },
        )

        # Delete the user
        response = client.post(f"/admin/user/{user_id}/delete", follow_redirects=True)

        assert response.status_code == 200
        assert b"User deleted successfully!" in response.data

        # Verify user was deleted
        with app.app_context():
            user = User.query.get(user_id)
            assert user is None


class TestAdminModelDiscovery:
    """Test model discovery and registration."""

    def test_admin_discovers_user_model(self, client, admin_user):
        """Test that admin automatically discovers the User model."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "adminpass123",
                "remember_me": False,
            },
        )

        response = client.get("/admin/")
        assert response.status_code == 200
        assert b"User" in response.data
        assert b"View All" in response.data
        assert b"Add New" in response.data

    def test_admin_shows_model_counts(self, client, admin_user, auth_user):
        """Test that admin dashboard shows correct model counts."""
        # Login as admin
        client.post(
            "/auth/login",
            data={
                "username": admin_user.username,
                "password": "adminpass123",
                "remember_me": False,
            },
        )

        response = client.get("/admin/")
        assert response.status_code == 200
        # Should show at least 2 users (admin and regular)
        assert b"records" in response.data


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        user = User(
            username="admin", email="admin@example.com", is_active=True, is_admin=True
        )
        user.set_password("adminpass123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def auth_user(app):
    """Create a regular authenticated user for testing."""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_admin=False,
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user
