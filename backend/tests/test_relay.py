import socket
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.windows_localhost_relay import open_upstream


def test_upload_socket_is_not_closed_after_five_seconds():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_and_wait():
        connection, _ = server.accept()
        connection.settimeout(2)
        try:
            connection.recv(8)
        except socket.timeout:
            pass
        connection.close()

    thread = threading.Thread(target=accept_and_wait, daemon=True)
    thread.start()
    upstream = open_upstream("127.0.0.1", port)
    try:
        assert upstream.gettimeout() is None
    finally:
        upstream.close()
        server.close()
        thread.join(timeout=2)
