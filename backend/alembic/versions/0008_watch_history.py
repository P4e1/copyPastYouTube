"""История просмотров зрителя."""

import sqlalchemy as sa
from alembic import op

revision = "0008_watch_history"
down_revision = "0007_media_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watch_history",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("watched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "video_id"),
    )


def downgrade() -> None:
    op.drop_table("watch_history")
