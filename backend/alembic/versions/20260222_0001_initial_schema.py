"""initial schema

Revision ID: 20260222_0001
Revises:
Create Date: 2026-02-22 22:45:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260222_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("google_id", sa.String(length=255), nullable=True),
        sa.Column("college", sa.String(length=300), nullable=True),
        sa.Column("degree", sa.String(length=200), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('student', 'admin')", name="ck_user_role"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_user_email"),
        sa.UniqueConstraint("google_id", name="uq_user_google_id"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_created_at", "users", ["created_at"])

    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("domain", sa.String(length=50), nullable=True),
        sa.Column("college", sa.String(length=300), nullable=True),
        sa.Column("member_count", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type IN ('domain', 'college', 'general')", name="ck_group_type"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_group_type", "groups", ["type"])

    op.create_table(
        "monitored_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("last_scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("scraper_config", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("type IN ('static', 'dynamic')", name="ck_source_type"),
        sa.CheckConstraint("interval_minutes >= 15", name="ck_source_interval_min"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_monitored_source_url"),
    )
    op.create_index("ix_sources_active", "monitored_sources", ["active"])

    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("institution", sa.String(length=300), nullable=True),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("secondary_domain", sa.String(length=50), nullable=True),
        sa.Column("classification_confidence", sa.Float(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("application_link", sa.String(length=2048), nullable=True),
        sa.Column("eligibility", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding_vector", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "domain IN ('ai_ds', 'cs', 'ece', 'me', 'civil', 'biotech', 'law', 'management', 'finance', 'humanities', 'govt', 'unclassified')",
            name="ck_opportunity_domain",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash", name="uq_opportunity_hash"),
    )
    op.create_index("ix_opp_domain", "opportunities", ["domain"])
    op.create_index("ix_opp_deadline", "opportunities", ["deadline"])
    op.create_index("ix_opp_institution", "opportunities", ["institution"])
    op.create_index("ix_opp_created_at", "opportunities", ["created_at"])
    op.create_index("ix_opp_is_active", "opportunities", ["is_active"])
    op.create_index("ix_opp_confidence", "opportunities", ["classification_confidence"])

    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.ARRAY(sa.String(length=100)), nullable=True),
        sa.Column("interests", postgresql.ARRAY(sa.String(length=100)), nullable=True),
        sa.Column("resume_path", sa.String(length=500), nullable=True),
        sa.Column("embedding_vector", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("github_url", sa.String(length=300), nullable=True),
        sa.Column("linkedin_url", sa.String(length=300), nullable=True),
        sa.Column("coding_profiles", sa.Text(), nullable=True),
        sa.Column("consent_to_autofill", sa.Boolean(), nullable=False),
        sa.Column("embedding_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_profile_user_id"),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("form_data_json", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'accepted', 'rejected', 'withdrawn')",
            name="ck_application_status",
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "opportunity_id", name="uq_application_user_opp"
        ),
    )
    op.create_index("ix_application_user_id", "applications", ["user_id"])
    op.create_index("ix_application_opportunity_id", "applications", ["opportunity_id"])
    op.create_index("ix_application_status", "applications", ["status"])

    op.create_table(
        "achievements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("proof_url", sa.String(length=2048), nullable=True),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("points_claimed", sa.Integer(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type IN ('hackathon', 'internship', 'publication', 'competition', 'certification', 'coding', 'community', 'other')",
            name="ck_achievement_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_achievement_user_id", "achievements", ["user_id"])
    op.create_index("ix_achievement_type", "achievements", ["type"])
    op.create_index("ix_achievement_verified", "achievements", ["verified"])

    op.create_table(
        "incoscore_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=True),
        sa.Column("components_json", sa.Text(), nullable=True),
        sa.Column("computation_version", sa.String(length=20), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "total_score >= 0 AND total_score <= 1000", name="ck_incoscore_range"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incoscore_user_id", "incoscore_history", ["user_id"])
    op.create_index("ix_incoscore_total", "incoscore_history", ["total_score"])
    op.create_index("ix_incoscore_domain", "incoscore_history", ["domain"])
    op.create_index("ix_incoscore_computed_at", "incoscore_history", ["computed_at"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("email_sent", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type IN ('opportunity_match', 'deadline_reminder', 'achievement_verified', 'score_change', 'community_reply', 'application_update', 'system')",
            name="ck_notification_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_user_id", "notifications", ["user_id"])
    op.create_index("ix_notification_read", "notifications", ["read"])
    op.create_index("ix_notification_created_at", "notifications", ["created_at"])

    op.create_table(
        "group_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('member', 'moderator', 'admin')", name="ck_group_member_role"
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )
    op.create_index("ix_group_member_user", "group_members", ["user_id"])
    op.create_index("ix_group_member_group", "group_members", ["group_id"])

    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("likes_count", sa.Integer(), nullable=False),
        sa.Column("comments_count", sa.Integer(), nullable=False),
        sa.Column("report_count", sa.Integer(), nullable=False),
        sa.Column("is_flagged", sa.Boolean(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_post_user_id", "posts", ["user_id"])
    op.create_index("ix_post_group_id", "posts", ["group_id"])
    op.create_index("ix_post_created_at", "posts", ["created_at"])
    op.create_index("ix_post_is_flagged", "posts", ["is_flagged"])

    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_flagged", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comment_post_id", "comments", ["post_id"])
    op.create_index("ix_comment_user_id", "comments", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_group_id", "messages", ["group_id"])
    op.create_index("ix_message_sender_id", "messages", ["sender_id"])
    op.create_index("ix_message_created_at", "messages", ["created_at"])


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("comments")
    op.drop_table("posts")
    op.drop_table("group_members")
    op.drop_table("notifications")
    op.drop_table("incoscore_history")
    op.drop_table("achievements")
    op.drop_table("applications")
    op.drop_table("profiles")
    op.drop_table("opportunities")
    op.drop_table("monitored_sources")
    op.drop_table("groups")
    op.drop_table("users")
