#!/usr/bin/env bash
# Первый порт начиная с предпочтительного, которого нет в списке занятых.
set -euo pipefail

preferred="${1:?}"
shift || true
declare -A taken=()
for port in "$@"; do
  [[ -n "$port" ]] || continue
  taken["$port"]=1
done

port="$preferred"
for _ in $(seq 1 30); do
  if [[ -z "${taken[$port]:-}" ]]; then
    printf '%s\n' "$port"
    exit 0
  fi
  port=$((port + 1))
done

echo "Нет свободного порта рядом с ${preferred}" >&2
exit 1
