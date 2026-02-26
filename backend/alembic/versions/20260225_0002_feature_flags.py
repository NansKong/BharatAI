"""Add feature_flags and flag_evaluations tables

Revision ID: 20260225_0002
Revises: 20260222_0001
Create Date: 2026-02-25
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20260225_0002"
down_revision = "20260222_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("rollout_percentage", sa.Float, nullable=False, server_default="0"),
        sa.Column("target_user_ids", postgresql.JSONB, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_table(
        "flag_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "flag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("feature_flags.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("flag_name", sa.String(100), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.Boolean, nullable=False),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Composite index for analytics queries
    op.create_index(
        "ix_flag_evaluations_name_result", "flag_evaluations", ["flag_name", "result"]
    )

    # Seed default flags
    op.execute(
        """
        INSERT INTO feature_flags (id, name, description, is_enabled, rollout_percentage, target_user_ids)
        VALUES
            (gen_random_uuid(), 'ai_classification',   'AI-powered opportunity classification',       false, 0, '[]'),
            (gen_random_uuid(), 'personalized_feed',    'Personalized opportunity feed ranking',       false, 0, '[]'),
            (gen_random_uuid(), 'incoscore_engine',     'InCoScore computation engine',                false, 0, '[]'),
            (gen_random_uuid(), 'community_features',   'Community posts, groups, and messaging',      false, 0, '[]'),
            (gen_random_uuid(), 'app_assistance',       'Application assistance and autofill',         false, 0, '[]'),
            (gen_random_uuid(), 'browser_automation',   'Browser automation for form filling',         false, 0, '[]')
        ON CONFLICT (name) DO NOTHING;
    """
    )


def downgrade() -> None:
    op.drop_index("ix_flag_evaluations_name_result", table_name="flag_evaluations")
    op.drop_table("flag_evaluations")
    op.drop_table("feature_flags")
