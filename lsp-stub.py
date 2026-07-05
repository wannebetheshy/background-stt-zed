#!/usr/bin/env python3
"""Minimal LSP stub that starts the STT HTTP server and keeps Zed's LSP slot alive."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any


HEALTH_URL = "http://127.0.0.1:8765/health"
LOGFILE = "/tmp/background-realtime-stt.log"


def ensure_server_running() -> None:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=1) as response:
            if response.status == 200:
                print("[background-realtime-stt] server already running", file=sys.stderr)
                return
    except (urllib.error.URLError, TimeoutError, OSError):
        pass

    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_dir = os.path.join(script_dir, "server")
    venv_dir = os.path.join(server_dir, ".venv")
    settings_path = os.path.join(server_dir, "settings.yaml")

    print(f"[background-realtime-stt] starting server, logs: {LOGFILE}", file=sys.stderr)
    command = (
        f'cd "{server_dir}" && '
        f'VENV_DIR="{venv_dir}" SETTINGS_PATH="{settings_path}" bash setup.sh'
    )
    subprocess.Popen(
        ["bash", "-c", command],
        stdout=open(LOGFILE, "a", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None

        decoded = line.decode("ascii").strip()
        if decoded == "":
            break

        name, value = decoded.split(": ", 1)
        headers[name.lower()] = value

    content_length = int(headers["content-length"])
    body = sys.stdin.buffer.read(content_length)
    return json.loads(body)


def write_message(payload: dict[str, Any]) -> None:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def handle_message(message: dict[str, Any]) -> bool:
    method = message.get("method")
    request_id = message.get("id")

    if request_id is None:
        if method == "exit":
            return False
        return True

    if method == "initialize":
        write_message(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "capabilities": {},
                    "serverInfo": {
                        "name": "background-realtime-stt-stub",
                        "version": "0.1.0",
                    },
                },
            }
        )
    elif method == "shutdown":
        write_message({"jsonrpc": "2.0", "id": request_id, "result": None})
    else:
        write_message({"jsonrpc": "2.0", "id": request_id, "result": None})

    return True


def main() -> None:
    ensure_server_running()

    while True:
        message = read_message()
        if message is None:
            break
        if not handle_message(message):
            break


if __name__ == "__main__":
    main()
