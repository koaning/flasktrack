"""Error handlers."""

from flask import render_template
from app import db


def not_found_error(error):
    """404 error handler."""
    return render_template('errors/404.html'), 404


def internal_error(error):
    """500 error handler."""
    db.session.rollback()
    return render_template('errors/500.html'), 500