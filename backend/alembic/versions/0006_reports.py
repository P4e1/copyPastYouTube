"""Таблица reports."""

import sqlalchemy as sa
from alembic import op

revision = "0006_reports"
down_revision = "0005_channels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("reporter_id", sa.String(length=36), nullable=False),
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("resolved_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"]),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_table("reports")
