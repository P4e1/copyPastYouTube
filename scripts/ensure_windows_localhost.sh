#!/usr/bin/env bash
# Поднять http://localhost:8080 в браузере Windows, если Docker слушает только внутри WSL.
set -euo pipefail

cd "$(dirname "$0")/.."

wsl_ip="$(hostname -I | awk '{print $1}')"
win_dir="$(cmd.exe /c "echo %LOCALAPPDATA%\\copypast-youtube" | tr -d '\r' | sed 's/[[:space:]]*$//')"
mkdir -p "$(wslpath -u "$win_dir")"
cp "$PWD/scripts/ensure_windows_localhost.ps1" "$PWD/scripts/windows_localhost_relay.py" "$(wslpath -u "$win_dir")/"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "${win_dir}\\ensure_windows_localhost.ps1" -WslIp "$wsl_ip" -Port "${1:-8080}"
