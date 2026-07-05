#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SERVER_DIR="${SCRIPT_DIR}/server"
VENV_DIR="${SERVER_DIR}/.venv"
SETTINGS_PATH="${SERVER_DIR}/settings.yaml"
PORT=8764
LOG="/tmp/background-realtime-stt.log"
WORKER_PID_FILE="/tmp/background-realtime-stt-worker.pid"

if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    echo "[background-realtime-stt] server already running on ${PORT}" >&2
    exit 0
fi

echo "[background-realtime-stt] starting server on ${PORT}, logs: ${LOG}" >&2

env VENV_DIR="${VENV_DIR}" SETTINGS_PATH="${SETTINGS_PATH}" \
    bash -c "cd \"${SERVER_DIR}\" && bash setup.sh" >>"${LOG}" 2>&1 &
echo $! >"${WORKER_PID_FILE}"
