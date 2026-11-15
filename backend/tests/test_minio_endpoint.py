"""Внутренний адрес MinIO берётся по IPv4, подключение повторяется."""

from app.infrastructure.minio_storage import call_with_retry, ipv4_netloc


def test_ipv4_netloc_uses_lookup():
    assert ipv4_netloc("minio:9000", lambda host, port: "10.0.0.8") == "10.0.0.8:9000"


def test_ipv4_netloc_keeps_localhost():
    assert ipv4_netloc("127.0.0.1:9000", lambda host, port: "10.0.0.8") == "127.0.0.1:9000"


def test_ipv4_netloc_keeps_name_when_lookup_fails():
    def boom(host, port):
        raise OSError(host)

    assert ipv4_netloc("minio:9000", boom) == "minio:9000"


def test_call_with_retry_returns_after_failure():
    pauses = []
    calls = {"n": 0}

    def action():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("нет связи")
        return "ok"

    assert call_with_retry(action, attempts=3, pause=2, sleep=pauses.append) == "ok"
    assert pauses == [2, 2]
