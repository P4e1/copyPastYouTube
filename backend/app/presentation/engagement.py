"""Маршруты просмотра, лайка и комментариев."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.domain.auth import InvalidCredentialsError

router = APIRouter()


class LikeIn(BaseModel):
    value: int


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    parent_id: str | None = None


class ViewOut(BaseModel):
    view_count: int


class LikeOut(BaseModel):
    value: int


class CommentOut(BaseModel):
    id: str
    user_id: str
    parent_id: str | None
    body: str


class CommentListOut(BaseModel):
    items: list[CommentOut]


def _account(request: Request):
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Требуется вход")
    try:
        return request.app.state.account_by_token(token.strip())
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _comment_out(comment) -> CommentOut:
    return CommentOut(
        id=comment.id,
        user_id=comment.user_id,
        parent_id=comment.parent_id,
        body=comment.body,
    )


@router.post("/videos/{video_id}/view", response_model=ViewOut)
def view_video(video_id: str, request: Request) -> ViewOut:
    account = _account(request)
    view_count = request.app.state.register_view(video_id, account.id)
    return ViewOut(view_count=view_count)


@router.post("/videos/{video_id}/like", response_model=LikeOut)
def like_video(video_id: str, body: LikeIn, request: Request) -> LikeOut:
    account = _account(request)
    value = request.app.state.register_like(video_id, account.id, body.value)
    return LikeOut(value=value)


@router.get("/videos/{video_id}/comments", response_model=CommentListOut)
def get_comments(video_id: str, request: Request) -> CommentListOut:
    account = _account(request)
    comments = request.app.state.comments_for_video(video_id, account.id)
    return CommentListOut(items=[_comment_out(comment) for comment in comments])


@router.post("/videos/{video_id}/comments", status_code=201, response_model=CommentOut)
def post_comment(video_id: str, body: CommentIn, request: Request) -> CommentOut:
    account = _account(request)
    comment = request.app.state.publish_comment(video_id, account.id, body.body, body.parent_id)
    return _comment_out(comment)


@router.delete("/videos/{video_id}/comments/{comment_id}", status_code=204)
def delete_comment(video_id: str, comment_id: str, request: Request) -> None:
    account = _account(request)
    request.app.state.delete_own_comment(video_id, comment_id, account.id)
