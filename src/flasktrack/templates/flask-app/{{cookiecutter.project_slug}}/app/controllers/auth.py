"""Authentication blueprint routes."""

import sys
from urllib.parse import urlparse

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message

from app import db, mail
from app.forms.auth import LoginForm, MagicLinkForm, RegistrationForm
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for("main.dashboard")
        return redirect(next_page)

    return render_template("auth/login.html", form=form)


@auth_bp.route('/magic-link', methods=['GET', 'POST'])
def magic_link():
    """Request a magic link for passwordless login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = MagicLinkForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        # Create user if they don't exist (optional - remove if you want existing users only)
        if not user:
            # Auto-generate username from email
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(username=username, email=email)
            db.session.add(user)

        # Generate magic link token
        token = user.generate_magic_link_token()
        db.session.commit()

        # Create the magic link URL
        magic_url = url_for('auth.verify_magic_link', token=token, _external=True)

        # Check if we should show link in terminal (local development)
        if current_app.config.get('SHOW_MAGIC_LINK_IN_TERMINAL', False):
            # Print to terminal with nice formatting
            print("\n" + "="*60, file=sys.stderr)
            print("MAGIC LINK LOGIN (Development Mode)", file=sys.stderr)
            print("="*60, file=sys.stderr)
            print(f"Email: {email}", file=sys.stderr)
            print(f"Magic Link: {magic_url}", file=sys.stderr)
            print("="*60 + "\n", file=sys.stderr)
            flash('Magic link displayed in terminal (development mode)', 'info')
        else:
            # Send email in production
            try:
                msg = Message(
                    'Your Magic Link to Login',
                    recipients=[email],
                    sender=current_app.config.get('MAIL_DEFAULT_SENDER')
                )
                msg.body = f'''Hello,

Click the link below to log in to your account:

{magic_url}

This link will expire in {current_app.config.get('MAGIC_LINK_EXPIRY_MINUTES', 15)} minutes.

If you didn't request this link, please ignore this email.

Best regards,
The {{ cookiecutter.project_name }} Team
'''
                msg.html = f'''<html>
<body>
    <p>Hello,</p>
    <p>Click the button below to log in to your account:</p>
    <p><a href="{magic_url}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Login to {{ cookiecutter.project_name }}</a></p>
    <p>Or copy and paste this link: <a href="{magic_url}">{magic_url}</a></p>
    <p>This link will expire in {current_app.config.get('MAGIC_LINK_EXPIRY_MINUTES', 15)} minutes.</p>
    <p>If you didn't request this link, please ignore this email.</p>
    <p>Best regards,<br>The {{ cookiecutter.project_name }} Team</p>
</body>
</html>'''
                mail.send(msg)
                flash(f'Magic link sent to {email}. Please check your email.', 'success')
            except Exception as e:
                current_app.logger.error(f"Failed to send magic link email: {str(e)}")
                flash('Failed to send magic link. Please try again.', 'danger')

        return redirect(url_for('auth.magic_link'))

    return render_template('auth/magic_link.html', form=form)


@auth_bp.route('/verify-magic-link/<token>')
def verify_magic_link(token):
    """Verify and login with magic link token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Find user with this token
    user = User.query.filter_by(magic_link_token=token).first()

    if not user:
        flash('Invalid or expired magic link.', 'danger')
        return redirect(url_for('auth.magic_link'))

    # Verify the token is valid and not expired
    if not user.verify_magic_link_token(token):
        flash('Invalid or expired magic link.', 'danger')
        return redirect(url_for('auth.magic_link'))

    # Clear the token and log the user in
    user.clear_magic_link_token()
    db.session.commit()

    login_user(user, remember=True)
    flash('Successfully logged in!', 'success')

    next_page = request.args.get('next')
    if not next_page or urlparse(next_page).netloc != '':
        next_page = url_for('main.dashboard')
    return redirect(next_page)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now registered!", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """User logout."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
