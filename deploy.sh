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
  else
    git -C "$dest" pull --ff-only origin "$REPO_REF"
  fi
  exec bash "$dest/deploy.sh"
fi

cd "$script_dir"

if ! command -v docker >/dev/null 2>&1; then
  echo "Нужен Docker с командой docker compose."
  exit 1
fi

bash "$script_dir/scripts/write_env.sh" "$script_dir/.env"

project_file="$script_dir/.compose-project"
if [[ -f "$project_file" ]]; then
  COMPOSE_PROJECT_NAME="$(tr -d '[:space:]' < "$project_file")"
else
  COMPOSE_PROJECT_NAME="$(bash "$script_dir/scripts/project_name.sh" "$script_dir")"
  printf '%s\n' "$COMPOSE_PROJECT_NAME" > "$project_file"
fi
export COMPOSE_PROJECT_NAME

env_get() {
  local key="$1" line
  line="$(grep -E "^${key}=" "$script_dir/.env" | tail -n 1 || true)"
  printf '%s' "${line#*=}"
}

env_set() {
  local key="$1" value="$2" file="$script_dir/.env"
  if grep -q "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

port_taken_by_other() {
  local port="$1" owners owner
  owners="$(docker ps --filter "publish=${port}" --format '{{.Label "com.docker.compose.project"}}' | sort -u)"
  if [[ -z "$owners" ]]; then
    if timeout 0.2 bash -c "echo >/dev/tcp/127.0.0.1/${port}" >/dev/null 2>&1; then
      return 0
    fi
    return 1
  fi
  while IFS= read -r owner; do
    [[ -z "$owner" ]] && continue
    if [[ "$owner" != "$COMPOSE_PROJECT_NAME" ]]; then
      return 0
    fi
  done <<< "$owners"
  return 1
}

busy_ports=()
for port in $(seq 8000 8030) $(seq 8080 8110) $(seq 9000 9030); do
  if port_taken_by_other "$port"; then
    busy_ports+=("$port")
  fi
done

pick() {
  bash "$script_dir/scripts/pick_port.sh" "$1" "${busy_ports[@]}"
}

front="$(env_get FRONTEND_PORT)"
api_port="$(env_get API_PORT)"
minio_port="$(env_get MINIO_PORT)"
console_port="$(env_get MINIO_CONSOLE_PORT)"
front="$(pick "${front:-8080}")"
busy_ports+=("$front")
api_port="$(pick "${api_port:-8000}")"
busy_ports+=("$api_port")
minio_port="$(pick "${minio_port:-9000}")"
busy_ports+=("$minio_port")
console_port="$(pick "${console_port:-9001}")"

env_set FRONTEND_PORT "$front"
env_set API_PORT "$api_port"
env_set MINIO_PORT "$minio_port"
env_set MINIO_CONSOLE_PORT "$console_port"
env_set CORS_ORIGINS "http://127.0.0.1:${front},http://localhost:${front}"
env_set MINIO_PUBLIC_ENDPOINT "http://localhost:${front}"

compose() {
  docker compose -p "$COMPOSE_PROJECT_NAME" "$@"
}

dump_logs() {
  echo "Состояние контейнеров и последние логи API, воркера и MinIO:"
  compose ps || true
  compose logs --tail 80 api worker minio || true
}

if ! compose build; then
  echo "Сборка образов не удалась. Поднимаю уже собранные локальные образы."
fi
if ! compose up -d --pull never; then
  dump_logs
  exit 1
fi

echo "Жду API и MinIO..."
ready=0
for _ in $(seq 1 60); do
  if compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"; then
    ready=1
    break
  fi
  sleep 2
done
if [[ "$ready" != 1 ]]; then
  echo "API не ответил на /health. Если это повторный каталог, он больше не использует чужой том PostgreSQL."
  dump_logs
  exit 1
fi

minio_ready=0
for _ in $(seq 1 60); do
  if compose exec -T api python -c "import os, urllib.request; urllib.request.urlopen(os.environ['MINIO_ENDPOINT'].rstrip('/') + '/minio/health/live', timeout=2)"; then
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

compose exec -T api alembic -c alembic.ini upgrade head
compose exec -T api python /scripts/seed.py

# Docker в WSL слушает порт, а браузер Windows ходит на свой localhost.
# Если проброс WSL не поднялся, Windows получает ERR_CONNECTION_REFUSED.
if grep -qi microsoft /proc/version 2>/dev/null; then
  bash "$PWD/scripts/ensure_windows_localhost.sh" "$front"
fi

echo "Готово: http://localhost:${front}"
