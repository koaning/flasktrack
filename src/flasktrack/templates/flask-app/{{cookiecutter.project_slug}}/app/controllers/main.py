"""Main blueprint routes."""

from flask import Blueprint, render_template
from flask_login import login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page."""
    return render_template('main/index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - requires authentication."""
    return render_template('main/dashboard.html')
