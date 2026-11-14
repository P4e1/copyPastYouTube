def test_health_returns_200_when_database_responds(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_docs_open(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_app_starts_without_storage_or_business_routers(app):
    import sys

    paths = set(app.openapi()["paths"])
    assert "/health" in paths
    business = {
        "/auth/register",
        "/auth/login",
        "/auth/me",
        "/videos",
        "/feed",
        "/search",
        "/playlists",
        "/reports",
    }
    assert paths.isdisjoint(business)
    loaded = set(sys.modules)
    assert "boto3" not in loaded
    assert "minio" not in loaded
    assert "ffmpeg" not in loaded
