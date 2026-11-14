def test_health_returns_200_when_database_responds(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_docs_open(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_app_exposes_health_and_auth_without_storage(app):
    import sys

    paths = set(app.openapi()["paths"])
    assert "/health" in paths
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/auth/me" in paths
    assert "/videos" in paths
    assert "/feed" in paths
    assert "/search" in paths
    assert "/playlists" in paths
    assert "/reports" in paths
    loaded = set(sys.modules)
    assert "boto3" not in loaded
    assert "ffmpeg" not in loaded


def test_cors_allows_only_frontend_origin(client):
    allowed = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})
    foreign = client.get("/health", headers={"Origin": "https://evil.example"})

    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "access-control-allow-origin" not in foreign.headers
