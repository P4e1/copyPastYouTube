"""Перевод доменных ошибок в статусы HTTP."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.domain.errors import ForbiddenError, NotFoundError, UploadRejected
from app.domain.security import PasswordTooWeak


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    def not_found(_request, exc: NotFoundError) -> JSONResponse:
        detail = str(exc) or "Не найдено"
        return JSONResponse(status_code=404, content={"detail": detail})

    @app.exception_handler(ForbiddenError)
    def forbidden(_request, exc: ForbiddenError) -> JSONResponse:
        detail = str(exc) or "Доступ запрещён"
        return JSONResponse(status_code=403, content={"detail": detail})

    @app.exception_handler(PasswordTooWeak)
    def password_too_weak(_request, exc: PasswordTooWeak) -> JSONResponse:
        detail = str(exc) or "Пароль должен быть от 8 до 200 символов"
        return JSONResponse(status_code=422, content={"detail": detail})

    @app.exception_handler(UploadRejected)
    def upload_rejected(_request, exc: UploadRejected) -> JSONResponse:
        detail = str(exc) or "Файл не принят"
        return JSONResponse(status_code=422, content={"detail": detail})
