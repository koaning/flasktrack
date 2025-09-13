"""User model."""

import secrets
from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    """User model for authentication."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(
        db.String(255), nullable=True
    )  # Made nullable for magic link users
    magic_link_token = db.Column(db.String(255), unique=True, nullable=True)
    magic_link_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        """Return True if user is authenticated."""
        return True

    @property
    def is_anonymous(self):
        """Return True if user is anonymous."""
        return False

    def get_id(self):
        """Return user id as string."""
        return str(self.id)

    def generate_magic_link_token(self):
        """Generate a magic link token with expiration."""
        self.magic_link_token = secrets.token_urlsafe(32)
        self.magic_link_expires = datetime.utcnow() + timedelta(minutes=15)
        return self.magic_link_token

    def verify_magic_link_token(self, token):
        """Verify if the magic link token is valid and not expired."""
        if not self.magic_link_token or not self.magic_link_expires:
            return False
        if self.magic_link_token != token:
            return False
        if datetime.utcnow() > self.magic_link_expires:  # noqa: SIM103
            return False
        return True

    def clear_magic_link_token(self):
        """Clear the magic link token after successful use."""
        self.magic_link_token = None
        self.magic_link_expires = None


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))
