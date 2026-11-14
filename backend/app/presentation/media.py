"""Маршруты завершения загрузки и ссылки на просмотр."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.domain.auth import InvalidCredentialsError

router = APIRouter()


class PlaybackOut(BaseModel):
    url: str


def _account(request: Request):
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Требуется вход")
    try:
        return request.app.state.account_by_token(token.strip())
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _viewer_id(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    try:
        return request.app.state.account_by_token(token.strip()).id
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/videos/{video_id}/complete")
def complete_video(video_id: str, request: Request) -> dict:
    account = _account(request)
    request.app.state.complete_upload(video_id, account.id)
    return {"status": "processing"}


@router.get("/videos/{video_id}/playback", response_model=PlaybackOut)
def playback(video_id: str, request: Request) -> PlaybackOut:
    return PlaybackOut(url=request.app.state.playback_url(video_id, _viewer_id(request)))
