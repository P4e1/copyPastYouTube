"""Локальный TCP-пересыльщик: Windows localhost → адрес, где слушает страница.

Запуск из корня репозитория: pytest scripts/test_windows_localhost_relay.py
"""

import importlib.util
import socket
import threading
from pathlib import Path


def load_relay():
    path = Path(__file__).resolve().parent / "windows_localhost_relay.py"
    spec = importlib.util.spec_from_file_location("windows_localhost_relay", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _listen() -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(8)
    return server


def test_relay_streams_both_directions_without_buffering_the_whole_body():
    relay_mod = load_relay()
    upstream = _listen()
    received = bytearray()
    released = threading.Event()

    def serve_upstream():
        conn, _ = upstream.accept()
        try:
            while len(received) < len(request):
                chunk = conn.recv(65536)
                if not chunk:
                    break
                received.extend(chunk)
            released.wait(2)
            conn.sendall(response)
        finally:
            conn.close()

    request = b"PUT /videos/clip.mp4 HTTP/1.1\r\nHost: localhost\r\n\r\n" + (b"v" * (256 * 1024))
    response = b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nready"
    thread = threading.Thread(target=serve_upstream)
    thread.start()

    relay = relay_mod.TcpRelay("127.0.0.1", 0, "127.0.0.1", upstream.getsockname()[1])
    relay.start()
    try:
        client = socket.create_connection(("127.0.0.1", relay.port), timeout=2)
        client.sendall(request)
        released.set()
        client.settimeout(2)
        got = bytearray()
        while len(got) < len(response):
            chunk = client.recv(65536)
            if not chunk:
                break
            got.extend(chunk)
        client.close()
    finally:
        relay.close()
        upstream.close()
        thread.join(2)

    assert bytes(received) == request
    assert bytes(got) == response


def test_relay_listens_on_the_requested_loopback_only():
    relay_mod = load_relay()
    upstream = _listen()
    relay = relay_mod.TcpRelay("127.0.0.1", 0, "127.0.0.1", upstream.getsockname()[1])
    relay.start()
    try:
        host, port = relay.listening
        assert host == "127.0.0.1"
        assert port == relay.port
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind(("127.0.0.1", port))
            occupied = False
        except OSError:
            occupied = True
        finally:
            probe.close()
        assert occupied is True
    finally:
        relay.close()
        upstream.close()
