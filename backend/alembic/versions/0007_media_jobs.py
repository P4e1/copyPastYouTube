"""Таблица media_jobs."""

import sqlalchemy as sa
from alembic import op

revision = "0007_media_jobs"
down_revision = "0006_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"]),
    )


def downgrade() -> None:
    op.drop_table("media_jobs")
