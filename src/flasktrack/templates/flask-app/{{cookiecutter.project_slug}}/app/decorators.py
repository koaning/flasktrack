"""Custom decorators for the application."""

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Decorator to require admin privileges for a route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            flash("You need administrator privileges to access this page.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)

    return decorated_function
