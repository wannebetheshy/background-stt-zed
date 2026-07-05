#!/usr/bin/env python3
"""Minimal MCP stub that starts the voice servers and keeps Zed's context-server slot alive."""

from __future__ import annotations

import atexit
import json
import os
import signal
import subprocess
import sys
from typing import Any

_server_stopped = False


def stop_server() -> None:
    global _server_stopped
    if _server_stopped:
        return
    _server_stopped = True

    script_dir = os.path.dirname(os.path.abspath(__file__))
    stop_script = os.path.join(script_dir, "stop-server.sh")
    subprocess.run(
        ["bash", stop_script],
        check=False,
    )


def register_shutdown_handlers() -> None:
    atexit.register(stop_server)

    def handle_signal(_signum: int, _frame: object | None) -> None:
        stop_server()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)


def ensure_server_running() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    start_script = os.path.join(script_dir, "start-server.sh")
    subprocess.Popen(
        ["bash", start_script],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None:
        return None

    if method == "initialize":
        ensure_server_running()
        params = message.get("params") or {}
        protocol_version = params.get("protocolVersion", "2024-11-05")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version,
                "capabilities": {},
                "serverInfo": {
                    "name": "background-realtime-stt",
                    "version": "0.1.0",
                },
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": []}}

    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"prompts": []}}

    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"resources": []}}

    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}

    return {"jsonrpc": "2.0", "id": request_id, "result": {}}


def main() -> None:
    register_shutdown_handlers()
    try:
        while True:
            message = read_message()
            if message is None:
                break

            response = handle_request(message)
            if response is not None:
                write_message(response)
    finally:
        stop_server()


if __name__ == "__main__":
    main()
