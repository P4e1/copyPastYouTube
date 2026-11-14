"""Подпись и чтение JWT. Секрет берётся из окружения."""

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.domain.auth import InvalidCredentialsError


def _secret() -> str:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError("Задайте JWT_SECRET")
    return secret


def _algorithm() -> str:
    return os.environ.get("JWT_ALGORITHM", "HS256")


def _ttl_minutes() -> int:
    return int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def issue_token(user_id: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=_ttl_minutes())
    return jwt.encode({"sub": user_id, "exp": expires}, _secret(), algorithm=_algorithm())


def read_user_id(token: str) -> str:
    try:
        payload = jwt.decode(token, _secret(), algorithms=[_algorithm()])
    except JWTError as exc:
        raise InvalidCredentialsError("Недействительный токен") from exc
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise InvalidCredentialsError("Недействительный токен")
    return user_id
