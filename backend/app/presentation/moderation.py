"""Маршруты жалоб, скрытия и назначения роли."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.domain.auth import InvalidCredentialsError, Role

router = APIRouter()


class ReportIn(BaseModel):
    video_id: str
    reason: str = Field(min_length=1, max_length=2000)


class ReportOut(BaseModel):
    id: str
    reporter_id: str
    video_id: str
    reason: str
    status: str


class ReportListOut(BaseModel):
    items: list[ReportOut]


class RoleIn(BaseModel):
    role: Role


class RoleOut(BaseModel):
    id: str
    role: str


def _account(request: Request):
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Требуется вход")
    try:
        return request.app.state.account_by_token(token.strip())
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _report_out(report) -> ReportOut:
    return ReportOut(
        id=report.id,
        reporter_id=report.reporter_id,
        video_id=report.video_id,
        reason=report.reason,
        status=report.status,
    )


@router.post("/reports", status_code=201, response_model=ReportOut)
def create_report(body: ReportIn, request: Request) -> ReportOut:
    account = _account(request)
    report = request.app.state.file_report(body.video_id, account.id, body.reason)
    return _report_out(report)


@router.get("/moderation/reports", response_model=ReportListOut)
def list_reports(request: Request) -> ReportListOut:
    account = _account(request)
    reports = request.app.state.queue_reports(account.role)
    return ReportListOut(items=[_report_out(report) for report in reports])


@router.post("/moderation/videos/{video_id}/hide")
def hide_video(video_id: str, request: Request) -> dict:
    account = _account(request)
    request.app.state.hide_reported_video(video_id, account.id, account.role)
    return {"status": "hidden"}


@router.post("/moderation/videos/{video_id}/restore")
def restore_video(video_id: str, request: Request) -> dict:
    account = _account(request)
    request.app.state.restore_hidden_video(video_id, account.role)
    return {"status": "ready"}


@router.patch("/admin/users/{user_id}/role", response_model=RoleOut)
def assign_role(user_id: str, body: RoleIn, request: Request) -> RoleOut:
    account = _account(request)
    role = request.app.state.change_user_role(account.role, user_id, body.role.value)
    return RoleOut(id=user_id, role=role)
