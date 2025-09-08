"""Test configuration."""

import os
import tempfile
import pytest
from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    """Create application for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # Clean up the temporary database file
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('testpass')
    db.session.add(user)
    db.session.commit()
    return user