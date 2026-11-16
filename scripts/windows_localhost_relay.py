"""TCP-пересыльщик: петля Windows → адрес, на котором страница уже слушает.

Слушает только переданный адрес. Байты идут в обе стороны по мере поступления,
без сборки всего тела запроса: так проходит и страница, и выгрузка ролика.
"""

import argparse
import socket
import threading


def open_upstream(target_host: str, target_port: int, connect_timeout: float = 5):
    """Соединение с целью. Таймаут только на установку, не на длинную выгрузку."""
    upstream = socket.create_connection((target_host, target_port), timeout=connect_timeout)
    upstream.settimeout(None)
    return upstream


def _pipe(src: socket.socket, dst: socket.socket) -> None:
    try:
        while True:
            chunk = src.recv(65536)
            if not chunk:
                break
            dst.sendall(chunk)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


class TcpRelay:
    def __init__(self, listen_host: str, listen_port: int, target_host: str, target_port: int):
        self._listen_host = listen_host
        self._listen_port = listen_port
        self._target_host = target_host
        self._target_port = target_port
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._closed = threading.Event()

    @property
    def port(self) -> int:
        return self.listening[1]

    @property
    def listening(self) -> tuple[str, int]:
        if self._socket is None:
            raise RuntimeError("relay is not started")
        host, port = self._socket.getsockname()
        return host, port

    def start(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self._listen_host, self._listen_port))
        sock.listen(128)
        sock.settimeout(0.2)
        self._socket = sock
        self._thread = threading.Thread(target=self._accept_loop, name="localhost-relay", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._closed.set()
        if self._socket is not None:
            self._socket.close()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _accept_loop(self) -> None:
        assert self._socket is not None
        while not self._closed.is_set():
            try:
                client, _ = self._socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle, args=(client,), daemon=True).start()

    def _handle(self, client: socket.socket) -> None:
        try:
            upstream = open_upstream(self._target_host, self._target_port)
        except OSError:
            client.close()
            return
        to_upstream = threading.Thread(target=_pipe, args=(client, upstream), daemon=True)
        to_client = threading.Thread(target=_pipe, args=(upstream, client), daemon=True)
        to_upstream.start()
        to_client.start()
        to_upstream.join()
        to_client.join()
        client.close()
        upstream.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Переслать localhost Windows на адрес WSL")
    parser.add_argument("--listen", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--target-port", type=int, required=True)
    args = parser.parse_args()
    relay = TcpRelay(args.listen, args.listen_port, args.target, args.target_port)
    relay.start()
    threading.Event().wait()


if __name__ == "__main__":
    main()
