"""Add email_prefs column to profiles table

Revision ID: 20260225_0003
Revises: 20260225_0002
Create Date: 2026-02-25
"""
from alembic import op

# revision identifiers
revision = "20260225_0003"
down_revision = "20260225_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use IF NOT EXISTS to be safe if column was already added manually or by Docker init
    op.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email_prefs TEXT")


def downgrade() -> None:
    op.drop_column("profiles", "email_prefs")
