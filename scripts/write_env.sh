#!/usr/bin/env bash
# Пишет .env со случайными секретами. Существующий файл не трогает.
set -euo pipefail

target="${1:-.env}"
if [[ -f "$target" ]]; then
  exit 0
fi

rand() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 24
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c 'import secrets; print(secrets.token_hex(24))'
  else
    od -An -N 24 -tx1 /dev/urandom | tr -d ' \n'
  fi
}

pg_pass="$(rand)"
minio_pass="$(rand)"
jwt_secret="$(rand)$(rand)"

umask 077
cat >"$target" <<EOF
POSTGRES_USER=youtube
POSTGRES_PASSWORD=${pg_pass}
POSTGRES_DB=youtube
DATABASE_URL=postgresql+psycopg://youtube:${pg_pass}@postgres:5432/youtube

MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=${minio_pass}
MINIO_ENDPOINT=http://minio:9000
MINIO_BUCKET=videos
MINIO_PUBLIC_ENDPOINT=http://localhost:8080

JWT_SECRET=${jwt_secret}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

MAX_UPLOAD_BYTES=2147483648

CORS_ORIGINS=http://127.0.0.1:8080,http://localhost:8080
EOF
