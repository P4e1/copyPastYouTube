"""Заголовки, политика пароля, лимит входа и отказ от шаблонного секрета."""

import os
import subprocess
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _registration() -> dict:
    mark = uuid.uuid4().hex
    return {
        "email": f"secure-{mark}@example.com",
        "username": f"secure{mark[:8]}",
        "password": "secret-pass",
    }


def test_short_password_is_rejected():
    from app.domain.security import PasswordTooWeak, ensure_password

    with pytest.raises(PasswordTooWeak):
        ensure_password("short")
    ensure_password("secret-pass")


def test_template_jwt_secret_is_rejected():
    from app.domain.security import ensure_jwt_secret

    with pytest.raises(RuntimeError):
        ensure_jwt_secret("change-me-jwt")
    with pytest.raises(RuntimeError):
        ensure_jwt_secret("short-secret")
    assert ensure_jwt_secret("test-jwt-secret-ok") == "test-jwt-secret-ok"


def test_register_rejects_a_short_password(client):
    payload = _registration()
    payload["password"] = "short"

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    assert "short" not in response.text


def test_unknown_email_and_wrong_password_look_the_same(client):
    payload = _registration()
    assert client.post("/auth/register", json=payload).status_code == 201

    wrong = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "wrong-pass"},
    )
    missing = client.post(
        "/auth/login",
        json={"email": f"missing-{uuid.uuid4().hex}@example.com", "password": "wrong-pass"},
    )

    assert wrong.status_code == 401
    assert missing.status_code == 401
    assert wrong.json()["detail"] == missing.json()["detail"]
    assert "password" not in wrong.json()


def test_api_sends_security_headers(client):
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_cors_does_not_open_for_a_foreign_site(client):
    response = client.get("/health", headers={"Origin": "https://evil.example"})

    assert response.headers.get("access-control-allow-origin") != "https://evil.example"


def test_login_burst_is_rejected():
    from starlette.responses import JSONResponse

    from app.presentation.security import AuthRateLimitMiddleware

    async def login(scope, receive, send):
        response = JSONResponse(status_code=401, content={"detail": "Неверный email или пароль"})
        await response(scope, receive, send)

    app = AuthRateLimitMiddleware(login, limit=3)

    import anyio
    from httpx import ASGITransport, AsyncClient

    async def burst():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            codes = []
            for _ in range(4):
                response = await http.post(
                    "/auth/login",
                    json={"email": "nobody@example.com", "password": "wrong-pass"},
                )
                codes.append(response.status_code)
            return codes

    codes = anyio.run(burst)
    assert codes[:3] == [401, 401, 401]
    assert codes[3] == 429


def test_frontend_proxy_sends_browser_headers():
    text = (ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")

    assert "X-Content-Type-Options" in text
    assert "nosniff" in text
    assert "X-Frame-Options" in text
    assert "Content-Security-Policy" in text
    assert "fonts.googleapis.com" in text
    assert "fonts.gstatic.com" in text


def test_api_image_does_not_run_as_root():
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "USER appuser" in text


def test_fresh_env_is_not_the_template(tmp_path):
    target = tmp_path / ".env"
    subprocess.check_call(["bash", str(ROOT / "scripts" / "write_env.sh"), str(target)])
    text = target.read_text(encoding="utf-8")

    assert "change-me" not in text
    secret = next(line.split("=", 1)[1] for line in text.splitlines() if line.startswith("JWT_SECRET="))
    assert len(secret) >= 32
    assert "POSTGRES_PASSWORD=" in text
    database = next(line for line in text.splitlines() if line.startswith("DATABASE_URL="))
    password = next(line.split("=", 1)[1] for line in text.splitlines() if line.startswith("POSTGRES_PASSWORD="))
    assert password in database


def test_deploy_script_clones_the_public_repo():
    text = (ROOT / "deploy.sh").read_text(encoding="utf-8")

    assert "https://github.com/P4e1/copyPastYouTube.git" in text
    assert "write_env.sh" in text
    assert "git clone" in text
    assert "project_name.sh" in text
    assert "COMPOSE_PROJECT_NAME" in text
    assert "pull --ff-only" in text


def test_each_checkout_gets_its_own_compose_project(tmp_path):
    first = tmp_path / "realese01" / "copyPastYouTube"
    second = tmp_path / "other" / "copyPastYouTube"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    script = ROOT / "scripts" / "project_name.sh"

    own = subprocess.check_output(["bash", str(script), str(first)], text=True).strip()
    other = subprocess.check_output(["bash", str(script), str(second)], text=True).strip()

    assert own.startswith("cpy-")
    assert "realese01" in own
    assert own != other


def test_taken_port_moves_to_the_next_free_one():
    script = ROOT / "scripts" / "pick_port.sh"
    taken = subprocess.check_output(["bash", str(script), "8080", "8080", "8000"], text=True).strip()
    free = subprocess.check_output(["bash", str(script), "8080"], text=True).strip()

    assert taken == "8081"
    assert free == "8080"


def test_compose_ports_follow_the_checkout_env():
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "${FRONTEND_PORT:-8080}:80" in text
    assert "${API_PORT:-8000}:8000" in text
    assert "${MINIO_PORT:-9000}:9000" in text
    assert "http://localhost:${FRONTEND_PORT:-8080}" in text
