#!/usr/bin/env bash
# Одна команда с чистой машины: скачать публичный репозиторий и поднять сервисы.
# Уже в каталоге проекта: bash deploy.sh
# С нуля: bash -c "$(curl -fsSL https://raw.githubusercontent.com/P4e1/copyPastYouTube/feature/youtube-clone/deploy.sh)"
set -euo pipefail

REPO_URL="${CPY_REPO:-https://github.com/P4e1/copyPastYouTube.git}"
REPO_REF="${CPY_REF:-feature/youtube-clone}"

script_path="${BASH_SOURCE[0]:-}"
script_dir=""
if [[ -n "$script_path" && -f "$script_path" ]]; then
  script_dir="$(cd "$(dirname "$script_path")" && pwd)"
fi

if [[ -z "$script_dir" || ! -f "$script_dir/docker-compose.yml" ]]; then
  if ! command -v git >/dev/null 2>&1; then
    echo "Нужен git, чтобы забрать ${REPO_URL}"
    exit 1
  fi
  dest="${CPY_DIR:-$PWD/copyPastYouTube}"
  if [[ ! -f "$dest/docker-compose.yml" ]]; then
    git clone --branch "$REPO_REF" --depth 1 "$REPO_URL" "$dest"
  fi
  exec bash "$dest/deploy.sh"
fi

cd "$script_dir"

if ! command -v docker >/dev/null 2>&1; then
  echo "Нужен Docker с командой docker compose."
  exit 1
fi

bash "$script_dir/scripts/write_env.sh" "$script_dir/.env"

dump_logs() {
  echo "Состояние контейнеров и последние логи API и MinIO:"
  docker compose ps || true
  docker compose logs --tail 120 api minio || true
}

if ! docker compose build; then
  echo "Сборка образов не удалась. Поднимаю уже собранные локальные образы."
fi
if ! docker compose up -d --pull never; then
  dump_logs
  exit 1
fi

echo "Жду API и MinIO..."
ready=0
for _ in $(seq 1 60); do
  if docker compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"; then
    ready=1
    break
  fi
  sleep 2
done
if [[ "$ready" != 1 ]]; then
  echo "API не ответил на /health"
  dump_logs
  exit 1
fi

minio_ready=0
for _ in $(seq 1 60); do
  if docker compose exec -T api python -c "import os, urllib.request; urllib.request.urlopen(os.environ['MINIO_ENDPOINT'].rstrip('/') + '/minio/health/live', timeout=2)"; then
    minio_ready=1
    break
  fi
  sleep 2
done
if [[ "$minio_ready" != 1 ]]; then
  echo "MinIO не ответил"
  dump_logs
  exit 1
fi

docker compose exec -T api alembic -c alembic.ini upgrade head
docker compose exec -T api python /scripts/seed.py

# Docker в WSL слушает порт, а браузер Windows ходит на свой localhost.
# Если проброс WSL не поднялся, Windows получает ERR_CONNECTION_REFUSED.
if grep -qi microsoft /proc/version 2>/dev/null; then
  bash "$PWD/scripts/ensure_windows_localhost.sh"
fi

echo "Готово: http://localhost:8080"
