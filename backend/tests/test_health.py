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
    later = {"/videos", "/feed", "/search", "/playlists", "/reports"}
    assert paths.isdisjoint(later)
    loaded = set(sys.modules)
    assert "boto3" not in loaded
    assert "minio" not in loaded
    assert "ffmpeg" not in loaded
