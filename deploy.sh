#!/usr/bin/env bash
set -euo pipefail

echo "deploy.sh — каркас спецификации."
echo "На шаге реализации эта команда выполнит:"
echo "  docker compose --profile later up --build -d"
echo "  миграции Alembic"
echo "  python scripts/seed.py"
echo "Сейчас образы приложения и схема БД не собраны. См. README.md."
exit 1
