"""Таблицы videos и video_grants."""

import sqlalchemy as sa
from alembic import op

revision = "0003_videos"
down_revision = "0002_users_channels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "videos",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("channel_id", sa.String(length=36), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("object_key", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_key", sa.String(length=500), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "video_grants",
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("video_id", "user_id"),
        sa.UniqueConstraint("video_id", "user_id", name="uq_video_grants_pair"),
    )


def downgrade() -> None:
    op.drop_table("video_grants")
    op.drop_table("videos")
