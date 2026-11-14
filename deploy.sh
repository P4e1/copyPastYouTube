#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

docker compose up --build -d

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
  exit 1
fi

docker compose exec -T api alembic -c alembic.ini upgrade head
docker compose exec -T api python /scripts/seed.py

echo "Готово: http://localhost:8080"
