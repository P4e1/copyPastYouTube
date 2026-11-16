#!/usr/bin/env bash
# Имя проекта Compose от полного пути каталога, чтобы второй клон не забрал чужой том.
set -euo pipefail

dir="$(cd "${1:-.}" && pwd -P)"
slug="$(printf '%s' "$dir" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-')"
slug="$(printf '%s' "$slug" | sed -e 's/^-*//' -e 's/-*$//' -e 's/-\{2,\}/-/g')"
if ((${#slug} > 50)); then
  slug="${slug: -50}"
  slug="${slug#-}"
fi
printf 'cpy-%s\n' "$slug"
