"""Репозиторий просмотров, лайков и комментариев."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.engagement import Comment
from app.infrastructure.engagement_models import CommentRow, LikeRow
from app.infrastructure.video_models import VideoRow


class SqlEngagementRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def increment_view(self, video_id: str) -> int:
        row = self._session.get(VideoRow, video_id)
        if row is None:
            raise RuntimeError("Ролик не найден")
        row.view_count += 1
        self._session.flush()
        return row.view_count

    def upsert_like(self, user_id: str, video_id: str, value: int) -> int:
        row = self._session.get(LikeRow, {"user_id": user_id, "video_id": video_id})
        if row is None:
            self._session.add(LikeRow(user_id=user_id, video_id=video_id, value=value))
        else:
            row.value = value
        self._session.flush()
        return value

    def add_comment(
        self,
        *,
        comment_id: str,
        video_id: str,
        user_id: str,
        parent_id: str | None,
        body: str,
    ) -> Comment:
        self._session.add(
            CommentRow(
                id=comment_id,
                video_id=video_id,
                user_id=user_id,
                parent_id=parent_id,
                body=body,
                is_hidden=False,
                created_at=datetime.now(timezone.utc),
            )
        )
        self._session.flush()
        return Comment(
            id=comment_id,
            video_id=video_id,
            user_id=user_id,
            parent_id=parent_id,
            body=body,
        )

    def list_comments(self, video_id: str) -> list[Comment]:
        rows = self._session.scalars(
            select(CommentRow)
            .where(CommentRow.video_id == video_id, CommentRow.is_hidden.is_(False))
            .order_by(CommentRow.created_at.asc())
        )
        return [
            Comment(
                id=row.id,
                video_id=row.video_id,
                user_id=row.user_id,
                parent_id=row.parent_id,
                body=row.body,
            )
            for row in rows
        ]

    def get_comment(self, comment_id: str) -> Comment | None:
        row = self._session.get(CommentRow, comment_id)
        if row is None:
            return None
        return Comment(
            id=row.id,
            video_id=row.video_id,
            user_id=row.user_id,
            parent_id=row.parent_id,
            body=row.body,
        )

    def delete_comment(self, comment_id: str) -> None:
        row = self._session.get(CommentRow, comment_id)
        if row is not None:
            self._session.delete(row)
            self._session.flush()
