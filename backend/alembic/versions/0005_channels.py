"""Таблицы subscriptions, playlists и playlist_items."""

import sqlalchemy as sa
from alembic import op

revision = "0005_channels"
down_revision = "0004_engagement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("subscriber_id", sa.String(length=36), nullable=False),
        sa.Column("channel_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["subscriber_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("subscriber_id", "channel_id"),
        sa.UniqueConstraint("subscriber_id", "channel_id", name="uq_subscriptions_pair"),
    )
    op.create_table(
        "playlists",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("channel_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "playlist_items",
        sa.Column("playlist_id", sa.String(length=36), nullable=False),
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("playlist_id", "video_id"),
        sa.UniqueConstraint("playlist_id", "video_id", name="uq_playlist_items_pair"),
    )


def downgrade() -> None:
    op.drop_table("playlist_items")
    op.drop_table("playlists")
    op.drop_table("subscriptions")
