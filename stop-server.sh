#!/usr/bin/env bash
set -euo pipefail

PORT=8764
NAME="background-realtime-stt"
WORKER_PID_FILE="/tmp/background-realtime-stt-worker.pid"

stop_process_tree() {
    local pid="$1"
    local signal="$2"
    local child

    if [[ -z "${pid}" ]] || ! kill -0 "${pid}" 2>/dev/null; then
        return 0
    fi

    for child in $(pgrep -P "${pid}" 2>/dev/null || true); do
        stop_process_tree "${child}" "${signal}"
    done

    kill "-${signal}" "${pid}" 2>/dev/null || kill "${pid}" 2>/dev/null || true
}

if [[ -f "${WORKER_PID_FILE}" ]]; then
    worker_pid="$(<"${WORKER_PID_FILE}")"
    if [[ -n "${worker_pid}" ]]; then
        echo "[${NAME}] stopping worker pid ${worker_pid}" >&2
        stop_process_tree "${worker_pid}" TERM
    fi
    rm -f "${WORKER_PID_FILE}"
fi

pids="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "${pids}" ]]; then
    echo "[${NAME}] stopping server on ${PORT} (pids: ${pids})" >&2
    kill ${pids} 2>/dev/null || true
fi

for _ in {1..10}; do
    if ! lsof -tiTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
        exit 0
    fi
    sleep 0.2
done

pids="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "${pids}" ]]; then
    echo "[${NAME}] force stopping server on ${PORT} (pids: ${pids})" >&2
    kill -9 ${pids} 2>/dev/null || true
fi
