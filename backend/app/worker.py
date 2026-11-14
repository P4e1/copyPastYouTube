"""Один проход или цикл очереди media_jobs.

Команда из каталога backend, с тем же окружением, что у API:

    python -m app.worker

Один проход без ожидания следующей задачи:

    python -m app.worker --once
"""

import sys
import time

from app.infrastructure.media_gateway import run_once


def main() -> None:
    once = "--once" in sys.argv
    while True:
        worked = run_once()
        if once:
            return
        if not worked:
            time.sleep(2)


if __name__ == "__main__":
    main()
