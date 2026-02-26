"""add scrape dead letters table

Revision ID: 20260222_0002
Revises: 20260222_0001
Create Date: 2026-02-22 23:40:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260222_0002"
down_revision: Union[str, None] = "20260222_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scrape_dead_letters",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_name", sa.String(length=200), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"], ["monitored_sources.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrape_dlq_source_id", "scrape_dead_letters", ["source_id"])
    op.create_index("ix_scrape_dlq_created_at", "scrape_dead_letters", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_scrape_dlq_created_at", table_name="scrape_dead_letters")
    op.drop_index("ix_scrape_dlq_source_id", table_name="scrape_dead_letters")
    op.drop_table("scrape_dead_letters")
