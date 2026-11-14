"""Таблицы videos и video_grants."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db import Base


class VideoRow(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(36), ForeignKey("channels.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    visibility: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class VideoGrantRow(Base):
    __tablename__ = "video_grants"
    __table_args__ = (UniqueConstraint("video_id", "user_id", name="uq_video_grants_pair"),)

    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("videos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
