"""Правила пароля, секрета JWT и окна попыток входа. Без HTTP и базы."""

import threading

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 200
MIN_JWT_SECRET_LENGTH = 16
WEAK_JWT_SECRETS = {
    "change-me",
    "change-me-jwt",
    "secret",
    "password",
    "jwt-secret",
}


class PasswordTooWeak(Exception):
    """Пароль короче политики сервиса."""


def ensure_password(password: str) -> None:
    """Принять пароль от 8 до 200 символов."""
    if not isinstance(password, str) or not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise PasswordTooWeak("Пароль должен быть от 8 до 200 символов")


def ensure_jwt_secret(secret: str | None) -> str:
    """Отклонить пустой, короткий и шаблонный секрет подписи."""
    value = (secret or "").strip()
    if len(value) < MIN_JWT_SECRET_LENGTH or value.lower() in WEAK_JWT_SECRETS:
        raise RuntimeError("JWT_SECRET слишком короткий или оставлен шаблоном")
    return value


class SlidingWindow:
    """Сколько событий ключа помещается в окно времени."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, *, limit: int, window: float, now: float) -> bool:
        with self._lock:
            fresh = [stamp for stamp in self._hits.get(key, []) if now - stamp < window]
            if len(fresh) >= limit:
                self._hits[key] = fresh
                return False
            fresh.append(now)
            self._hits[key] = fresh
            return True
