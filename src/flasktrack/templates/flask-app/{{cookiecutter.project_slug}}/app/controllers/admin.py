"""Admin blueprint for managing models."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from app import db
from app.admin.forms import generate_form_class
from app.admin.registry import model_registry
from app.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_required
def dashboard():
    """Admin dashboard showing all available models."""
    models = model_registry.get_all_models()

    # Get counts for each model
    model_stats = {}
    for model_name, model_info in models.items():
        model_class = model_info["class"]
        count = db.session.query(func.count(model_class.id)).scalar()
        model_stats[model_name] = {
            "name": model_info["name"],
            "count": count,
            "tablename": model_info["tablename"],
        }

    return render_template("admin/dashboard.html", models=model_stats)


@admin_bp.route("/<model_name>/")
@admin_required
def model_list(model_name):
    """List all records for a model."""
    model_class = model_registry.get_model(model_name)

    if not model_class:
        flash(f"Model '{model_name}' not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    # Get pagination parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)

    # Query with pagination
    query = db.session.query(model_class)
    pagination = db.paginate(
        query, page=page, per_page=per_page, error_out=False, max_per_page=100
    )

    # Get column information for display
    columns = model_registry.get_model_columns(model_class)

    return render_template(
        "admin/model_list.html",
        model_name=model_name,
        model_display_name=model_class.__name__,
        items=pagination.items,
        pagination=pagination,
        columns=columns,
    )


@admin_bp.route("/<model_name>/new", methods=["GET", "POST"])
@admin_required
def model_create(model_name):
    """Create a new record for a model."""
    model_class = model_registry.get_model(model_name)

    if not model_class:
        flash(f"Model '{model_name}' not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    # Generate form dynamically
    form_class = generate_form_class(model_class)
    form = form_class()

    if form.validate_on_submit():
        # Create new instance
        instance = model_class()

        # Set values from form
        for field_name, field in form._fields.items():
            # Skip CSRF token
            if field_name == "csrf_token":
                continue

            # Handle password field specially for User model
            if field_name == "password" and model_class.__name__ == "User":
                if field.data:  # Only set password if provided
                    if hasattr(instance, "set_password"):
                        instance.set_password(field.data)
                    else:
                        # Fallback if no set_password method
                        from werkzeug.security import generate_password_hash

                        instance.password_hash = generate_password_hash(field.data)
            elif hasattr(instance, field_name):
                # Handle None values for foreign keys
                value = field.data
                if value == "" or (isinstance(value, str) and value.lower() == "none"):
                    value = None
                setattr(instance, field_name, value)

        try:
            db.session.add(instance)
            db.session.commit()
            flash(f"{model_class.__name__} created successfully!", "success")
            return redirect(url_for("admin.model_list", model_name=model_name))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating {model_class.__name__}: {str(e)}", "danger")

    return render_template(
        "admin/model_form.html",
        form=form,
        model_name=model_name,
        model_display_name=model_class.__name__,
        action="Create",
    )


@admin_bp.route("/<model_name>/<int:id>/edit", methods=["GET", "POST"])
@admin_required
def model_edit(model_name, id):
    """Edit an existing record."""
    model_class = model_registry.get_model(model_name)

    if not model_class:
        flash(f"Model '{model_name}' not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    instance = db.session.query(model_class).get_or_404(id)

    # Generate form and populate with instance data
    form_class = generate_form_class(model_class)
    form = form_class(obj=instance)

    if form.validate_on_submit():
        # Update instance with form data
        for field_name, field in form._fields.items():
            # Skip CSRF token
            if field_name == "csrf_token":
                continue

            # Handle password field specially for User model
            if field_name == "password" and model_class.__name__ == "User":
                if field.data:  # Only update password if provided
                    if hasattr(instance, "set_password"):
                        instance.set_password(field.data)
                    else:
                        # Fallback if no set_password method
                        from werkzeug.security import generate_password_hash

                        instance.password_hash = generate_password_hash(field.data)
                # Skip if password field is empty (keep existing password)
            elif hasattr(instance, field_name):
                # Handle None values for foreign keys
                value = field.data
                if value == "" or (isinstance(value, str) and value.lower() == "none"):
                    value = None
                setattr(instance, field_name, value)

        try:
            db.session.commit()
            flash(f"{model_class.__name__} updated successfully!", "success")
            return redirect(url_for("admin.model_list", model_name=model_name))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating {model_class.__name__}: {str(e)}", "danger")

    return render_template(
        "admin/model_form.html",
        form=form,
        model_name=model_name,
        model_display_name=model_class.__name__,
        action="Edit",
        instance=instance,
    )


@admin_bp.route("/<model_name>/<int:id>/delete", methods=["POST"])
@admin_required
def model_delete(model_name, id):
    """Delete a record."""
    model_class = model_registry.get_model(model_name)

    if not model_class:
        flash(f"Model '{model_name}' not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    instance = db.session.query(model_class).get_or_404(id)

    try:
        db.session.delete(instance)
        db.session.commit()
        flash(f"{model_class.__name__} deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting {model_class.__name__}: {str(e)}", "danger")

    return redirect(url_for("admin.model_list", model_name=model_name))
