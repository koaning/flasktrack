"""Dynamic form generation for admin interface."""

from flask_wtf import FlaskForm
from sqlalchemy import inspect
from wtforms import (
    BooleanField,
    DateField,
    DateTimeField,
    DecimalField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Optional


def get_field_for_column(column):
    """Map SQLAlchemy column types to WTForms fields."""
    type_name = column.type.__class__.__name__

    type_mapping = {
        "String": StringField,
        "Text": TextAreaField,
        "Integer": IntegerField,
        "Float": FloatField,
        "Numeric": DecimalField,
        "Boolean": BooleanField,
        "Date": DateField,
        "DateTime": DateTimeField,
    }

    # Special handling for password fields
    if "password" in column.name.lower():
        return PasswordField

    return type_mapping.get(type_name, StringField)


def get_validators_for_column(column):
    """Generate validators based on column constraints."""
    validators = []

    if not column.nullable and not column.primary_key:
        validators.append(DataRequired())
    else:
        validators.append(Optional())

    # Add length validator for string fields
    if hasattr(column.type, "length") and column.type.length:
        validators.append(Length(max=column.type.length))

    # Add email validator for email fields
    if "email" in column.name.lower():
        validators.append(Email())

    return validators


def create_relationship_field(column, related_model):
    """Create a SelectField for foreign key relationships."""
    from app import db

    # Get choices immediately
    choices = []

    # Only add the empty option if the field is nullable
    if column.nullable:
        choices.append(("", "-- Select --"))

    if related_model:
        items = db.session.query(related_model).all()
        for item in items:
            # Try to get a reasonable display value
            if hasattr(item, "name"):
                label = item.name
            elif hasattr(item, "title"):
                label = item.title
            elif hasattr(item, "username"):
                label = item.username
            elif hasattr(item, "email"):
                label = item.email
            else:
                label = f"{related_model.__name__} #{item.id}"

            choices.append((item.id, str(label)))

    # Determine validators based on nullability
    validators = []
    if not column.nullable:
        validators.append(DataRequired())
    else:
        validators.append(Optional())

    # Use coerce=int only when we have actual values, use str for empty option
    def coerce_func(value):
        if value == "":
            return None
        return int(value)

    field = SelectField(
        label=column.name.replace("_id", "").replace("_", " ").title(),
        coerce=coerce_func,
        choices=choices,
        validators=validators,
    )
    return field


def generate_form_class(model):
    """Dynamically generate a WTForms class from a SQLAlchemy model."""
    mapper = inspect(model)

    # Build form fields dictionary
    form_fields = {}

    # Check if this is a User model - handle password specially
    is_user_model = model.__name__ == "User"

    # Fields that should never be editable in admin
    skip_fields = [
        "created_at",
        "updated_at",
        "magic_link_token",
        "magic_link_expires",
    ]

    for column in mapper.columns:
        # Skip primary key and system/internal fields
        if column.primary_key or column.name in skip_fields:
            continue

        # Skip password_hash field for User model - we'll add a password field instead
        if column.name == "password_hash" and is_user_model:
            continue

        # Handle foreign keys
        if column.foreign_keys:
            # Try to find the related model
            related_model = None
            for fk in column.foreign_keys:
                table_name = fk.column.table.name
                # Import all models to find the related one
                from app.admin.registry import model_registry

                for model_info in model_registry.get_all_models().values():
                    if model_info["tablename"] == table_name:
                        related_model = model_info["class"]
                        break

            field = create_relationship_field(column, related_model)
        else:
            # Regular field
            field_class = get_field_for_column(column)
            validators = get_validators_for_column(column)

            # Create field with proper label
            label = column.name.replace("_", " ").title()

            # Special handling for boolean fields (no validators needed)
            if field_class == BooleanField:
                field = field_class(label=label)
            else:
                field = field_class(label=label, validators=validators)

        form_fields[column.name] = field

    # Add password field for User model (not password_hash)
    if is_user_model:
        form_fields["password"] = PasswordField(
            label="Password",
            validators=[Optional(), Length(min=6, max=128)],
            description="Leave blank to keep existing password",
        )

    # Create and return the form class
    form_class = type(f"{model.__name__}Form", (FlaskForm,), form_fields)
    return form_class
