#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="/tmp/background-realtime-stt-mcp.log"
WATCHDOG_PID=""

find_supervisor_pid() {
    local pid="${PPID}"
    while [[ "${pid}" -gt 1 ]]; do
        local command
        command="$(ps -o command= -p "${pid}" 2>/dev/null || true)"
        if [[ "${command}" == *"/zed "* || "${command}" == *"/zed" || "${command}" == zed* ]]; then
            echo "${pid}"
            return 0
        fi
        pid="$(ps -o ppid= -p "${pid}" | tr -d ' ')"
    done
    echo "${PPID}"
}

SUPERVISOR_PID="$(find_supervisor_pid)"

stop_voice_server() {
    bash "${SCRIPT_DIR}/stop-server.sh" >>"${LOG}" 2>&1 || true
}

watch_supervisor() {
    while kill -0 "${SUPERVISOR_PID}" 2>/dev/null; do
        sleep 1
    done
    stop_voice_server
}

watch_supervisor &
WATCHDOG_PID=$!

trap 'kill "${WATCHDOG_PID}" 2>/dev/null || true' EXIT INT TERM

bash "${SCRIPT_DIR}/start-server.sh" >>"${LOG}" 2>&1 &
python3 -u "${SCRIPT_DIR}/mcp-stub.py"
