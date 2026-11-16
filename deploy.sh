#!/usr/bin/env bash
# Одна команда с чистой Ubuntu: поставить git и Docker (с compose), скачать репозиторий и поднять сервисы.
# Уже в каталоге проекта: bash deploy.sh
# С нуля: bash -c "$(curl -fsSL https://raw.githubusercontent.com/P4e1/copyPastYouTube/feature/youtube-clone/deploy.sh)"
set -euo pipefail

REPO_URL="${CPY_REPO:-https://github.com/P4e1/copyPastYouTube.git}"
REPO_REF="${CPY_REF:-feature/youtube-clone}"

log() { printf '\n==> %s\n' "$*"; }

# --- root / sudo -------------------------------------------------------------
SUDO=""
if [[ "$(id -u)" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    echo "Нужен root или sudo для установки пакетов."
    exit 1
  fi
fi

apt_install() {
  $SUDO apt-get update -y
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
}

# --- git ---------------------------------------------------------------------
ensure_git() {
  if ! command -v git >/dev/null 2>&1; then
    log "Устанавливаю git"
    apt_install git ca-certificates curl
  fi
}

# --- Docker ------------------------------------------------------------------
add_docker_repo() {
  # shellcheck disable=SC1091
  . /etc/os-release
  case "${ID:-}" in
    ubuntu|debian) ;;
    *) echo "Автоустановка Docker поддерживает только Ubuntu/Debian (у вас: ${ID:-unknown})."; exit 1 ;;
  esac
  local codename="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"
  apt_install ca-certificates curl
  $SUDO install -m 0755 -d /etc/apt/keyrings
  $SUDO curl -fsSL "https://download.docker.com/linux/${ID}/gpg" -o /etc/apt/keyrings/docker.asc
  $SUDO chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${ID} ${codename} stable" \
    | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null
}

ensure_docker_installed() {
  if ! command -v docker >/dev/null 2>&1; then
    log "Устанавливаю Docker Engine и compose-плагин"
    add_docker_repo
    apt_install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  elif ! docker compose version >/dev/null 2>&1 && ! $SUDO docker compose version >/dev/null 2>&1; then
    log "Docker есть, но нет compose-плагина. Ставлю"
    add_docker_repo
    apt_install docker-compose-plugin
  fi
}

start_docker_daemon() {
  if $SUDO docker info >/dev/null 2>&1; then
    return 0
  fi
  log "Запускаю демон Docker"
  if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    $SUDO systemctl enable --now docker
  else
    # WSL без systemd и подобные окружения
    $SUDO service docker start
  fi
  for _ in $(seq 1 30); do
    if $SUDO docker info >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Демон Docker не запустился."
  exit 1
}

ensure_docker_access() {
  # Обычному пользователю нужна группа docker. Без перелогина используем sg.
  if docker info >/dev/null 2>&1; then
    return 0
  fi
  if [[ "$(id -u)" -eq 0 ]]; then
    echo "Docker недоступен даже от root."
    exit 1
  fi
  if [[ -n "${CPY_DOCKER_REEXEC:-}" ]]; then
    echo "Нет доступа к Docker. Выйдите и зайдите в систему заново (или выполните: newgrp docker) и повторите запуск."
    exit 1
  fi
  log "Добавляю ${USER} в группу docker"
  $SUDO usermod -aG docker "$USER"
  export CPY_DOCKER_REEXEC=1
  exec sg docker -c "bash $(printf '%q' "$script_dir/deploy.sh")"
}

# --- получение репозитория ---------------------------------------------------
script_path="${BASH_SOURCE[0]:-}"
script_dir=""
if [[ -n "$script_path" && -f "$script_path" ]]; then
  script_dir="$(cd "$(dirname "$script_path")" && pwd)"
fi

if [[ -z "$script_dir" || ! -f "$script_dir/docker-compose.yml" ]]; then
  ensure_git
  dest="${CPY_DIR:-$PWD/copyPastYouTube}"
  if [[ ! -f "$dest/docker-compose.yml" ]]; then
    git clone --branch "$REPO_REF" --depth 1 "$REPO_URL" "$dest"
  else
    git -C "$dest" pull --ff-only origin "$REPO_REF"
  fi
  exec bash "$dest/deploy.sh"
fi

cd "$script_dir"

ensure_docker_installed
start_docker_daemon
ensure_docker_access

if ! docker compose version >/dev/null 2>&1; then
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

# Скачиваем готовые образы (postgres, minio). На чистой машине их нет,
# а ниже стоит --pull never. Ошибка не фатальна: образы могли быть скачаны ранее.
log "Скачиваю образы сервисов (PostgreSQL, MinIO)"
if ! compose pull --ignore-buildable; then
  echo "Не удалось скачать часть образов. Продолжаю с тем, что есть локально."
fi

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