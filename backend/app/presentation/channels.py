"""Маршруты канала, подписки и плейлистов."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.domain.auth import InvalidCredentialsError
from app.domain.videos import Visibility

router = APIRouter()


class ChannelVideoOut(BaseModel):
    id: str
    title: str
    status: str
    visibility: str
    hidden_mark: bool


class ChannelOut(BaseModel):
    id: str
    name: str
    description: str
    subscriber_count: int
    videos: list[ChannelVideoOut]


class RenameIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class PlaylistIn(BaseModel):
    channel_id: str
    title: str = Field(min_length=1, max_length=200)
    visibility: Visibility = Visibility.public


class PlaylistItemIn(BaseModel):
    video_id: str
    position: int = Field(ge=1)


class PlaylistItemOut(BaseModel):
    video_id: str
    position: int


class PlaylistOut(BaseModel):
    id: str
    channel_id: str
    title: str
    visibility: str
    items: list[PlaylistItemOut]


class PlaylistListOut(BaseModel):
    items: list[PlaylistOut]


def _account(request: Request):
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Требуется вход")
    try:
        return request.app.state.account_by_token(token.strip())
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _optional_viewer(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    account = request.app.state.account_by_token(token.strip())
    return account.id


def _playlist_out(card) -> PlaylistOut:
    return PlaylistOut(
        id=card.id,
        channel_id=card.channel_id,
        title=card.title,
        visibility=card.visibility,
        items=[PlaylistItemOut(video_id=item.video_id, position=item.position) for item in card.items],
    )


@router.get("/channels/{channel_id}", response_model=ChannelOut)
def get_channel(channel_id: str, request: Request) -> ChannelOut:
    card = request.app.state.channel_card(channel_id, _optional_viewer(request))
    return ChannelOut(
        id=card.id,
        name=card.name,
        description=card.description,
        subscriber_count=card.subscriber_count,
        videos=[
            ChannelVideoOut(
                id=video.id,
                title=video.title,
                status=video.status,
                visibility=video.visibility,
                hidden_mark=video.hidden_mark,
            )
            for video in card.videos
        ],
    )


@router.patch("/channels/{channel_id}", response_model=ChannelOut)
def rename_channel(channel_id: str, body: RenameIn, request: Request) -> ChannelOut:
    account = _account(request)
    request.app.state.update_channel_name(channel_id, account.id, body.name)
    return get_channel(channel_id, request)


@router.post("/channels/{channel_id}/subscribe")
def subscribe(channel_id: str, request: Request) -> dict:
    account = _account(request)
    request.app.state.subscribe_channel(channel_id, account.id)
    return {"subscribed": True}


@router.delete("/channels/{channel_id}/subscribe")
def unsubscribe(channel_id: str, request: Request) -> dict:
    account = _account(request)
    request.app.state.unsubscribe_channel(channel_id, account.id)
    return {"subscribed": False}


@router.get("/playlists", response_model=PlaylistListOut)
def list_playlists(channel_id: str, request: Request) -> PlaylistListOut:
    cards = request.app.state.channel_playlists(channel_id, _optional_viewer(request))
    return PlaylistListOut(items=[_playlist_out(card) for card in cards])


@router.post("/playlists", status_code=201, response_model=PlaylistOut)
def create_playlist(body: PlaylistIn, request: Request) -> PlaylistOut:
    account = _account(request)
    card = request.app.state.open_playlist(body.channel_id, account.id, body.title, body.visibility.value)
    return _playlist_out(card)


@router.post("/playlists/{playlist_id}/items", status_code=201)
def add_playlist_item(playlist_id: str, body: PlaylistItemIn, request: Request) -> dict:
    account = _account(request)
    request.app.state.place_playlist_item(playlist_id, account.id, body.video_id, body.position)
    return {"video_id": body.video_id, "position": body.position}
