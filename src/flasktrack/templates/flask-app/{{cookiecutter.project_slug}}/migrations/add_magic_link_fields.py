"""Add magic link fields to user table

This migration adds magic_link_token and magic_link_expires fields to the users table.
Run this migration with: flask db upgrade
"""

import sqlalchemy as sa
from alembic import op


def upgrade():
    """Add magic link fields to users table."""
    op.add_column('users', sa.Column('magic_link_token', sa.String(255), unique=True, nullable=True))
    op.add_column('users', sa.Column('magic_link_expires', sa.DateTime(), nullable=True))

    # Make password_hash nullable for magic link only users
    op.alter_column('users', 'password_hash', existing_type=sa.String(255), nullable=True)


def downgrade():
    """Remove magic link fields from users table."""
    op.drop_column('users', 'magic_link_token')
    op.drop_column('users', 'magic_link_expires')

    # Restore password_hash to non-nullable
    op.alter_column('users', 'password_hash', existing_type=sa.String(255), nullable=False)
