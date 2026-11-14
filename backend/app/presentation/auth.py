"""HTTP-маршруты регистрации, входа и текущего пользователя."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.domain.auth import Account, EmailTakenError, InvalidCredentialsError

router = APIRouter(prefix="/auth")


class RegisterIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class LoginIn(BaseModel):
    email: str
    password: str


class AccountOut(BaseModel):
    id: str
    email: str
    username: str
    role: str
    channel_id: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AccountOut


def _account_out(account: Account) -> AccountOut:
    return AccountOut(
        id=account.id,
        email=account.email,
        username=account.username,
        role=account.role,
        channel_id=account.channel_id,
    )


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


@router.post("/register", status_code=201, response_model=AccountOut)
def register(body: RegisterIn, request: Request) -> AccountOut:
    try:
        account = request.app.state.register_account(body.email, body.username, body.password)
    except EmailTakenError as exc:
        raise _http_error(409, str(exc)) from exc
    return _account_out(account)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request) -> TokenOut:
    try:
        account, token = request.app.state.login_account(body.email, body.password)
    except InvalidCredentialsError as exc:
        raise _http_error(401, str(exc)) from exc
    return TokenOut(access_token=token, user=_account_out(account))


@router.get("/me", response_model=AccountOut)
def me(request: Request) -> AccountOut:
    token = _bearer_token(request)
    if token is None:
        raise _http_error(401, "Требуется вход")
    try:
        account = request.app.state.account_by_token(token)
    except InvalidCredentialsError as exc:
        raise _http_error(401, str(exc)) from exc
    return _account_out(account)


def _http_error(status_code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)
