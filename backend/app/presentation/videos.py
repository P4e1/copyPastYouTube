"""Маршруты создания ролика, карточки, ленты и поиска."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.domain.auth import InvalidCredentialsError
from app.domain.errors import NotFoundError
from app.domain.videos import Visibility

router = APIRouter()


class CreateVideoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    visibility: Visibility
    grant_user_ids: list[str] = Field(default_factory=list)


class VideoOut(BaseModel):
    id: str
    title: str
    description: str
    visibility: str
    status: str
    object_key: str
    channel_id: str
    hidden_mark: bool
    upload_url: str | None = None
    view_count: int = 0
    duration_sec: int = 0
    created_at: str = ""
    channel_name: str = ""
    thumbnail_url: str | None = None


class VideoListOut(BaseModel):
    items: list[VideoOut]


def _viewer_id(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    try:
        account = request.app.state.account_by_token(token.strip())
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return account.id


def _required_account(request: Request):
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Требуется вход")
    try:
        return request.app.state.account_by_token(token.strip())
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _out(card, upload_url: str | None = None) -> VideoOut:
    return VideoOut(
        id=card.id,
        title=card.title,
        description=card.description,
        visibility=card.visibility,
        status=card.status,
        object_key=card.object_key,
        channel_id=card.channel_id,
        hidden_mark=card.hidden_mark,
        upload_url=upload_url,
        view_count=card.view_count,
        duration_sec=card.duration_sec,
        created_at=card.created_at,
        channel_name=card.channel_name,
        thumbnail_url=card.thumbnail_url,
    )


class UpdateVideoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    visibility: Visibility
    grant_user_ids: list[str] = Field(default_factory=list)


@router.post("/videos", status_code=201, response_model=VideoOut)
def create_video(body: CreateVideoIn, request: Request) -> VideoOut:
    account = _required_account(request)
    card, upload_url = request.app.state.create_video(
        channel_id=account.channel_id,
        owner_id=account.id,
        title=body.title,
        description=body.description,
        visibility=body.visibility.value,
        grant_user_ids=body.grant_user_ids,
    )
    return _out(card, upload_url)


@router.patch("/videos/{video_id}", response_model=VideoOut)
def update_video(video_id: str, body: UpdateVideoIn, request: Request) -> VideoOut:
    account = _required_account(request)
    card = request.app.state.revise_video(
        video_id,
        account.id,
        title=body.title,
        description=body.description,
        visibility=body.visibility.value,
        grant_user_ids=body.grant_user_ids,
    )
    return _out(card)


@router.get("/videos/{video_id}", response_model=VideoOut)
def get_video(video_id: str, request: Request) -> VideoOut:
    try:
        card = request.app.state.get_video(video_id, _viewer_id(request))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _out(card)


@router.get("/feed", response_model=VideoListOut)
def feed(request: Request) -> VideoListOut:
    return VideoListOut(items=[_out(card) for card in request.app.state.list_feed()])


@router.get("/history", response_model=VideoListOut)
def history(request: Request) -> VideoListOut:
    account = _required_account(request)
    return VideoListOut(items=[_out(card) for card in request.app.state.list_history(account.id)])


@router.get("/search", response_model=VideoListOut)
def search(q: str, request: Request) -> VideoListOut:
    return VideoListOut(items=[_out(card) for card in request.app.state.search_videos(q)])
