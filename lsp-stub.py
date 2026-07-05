#!/usr/bin/env python3
"""Minimal LSP stub that starts the voice servers and keeps Zed's LSP slot alive."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any


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


def handle_message(message: dict[str, Any]) -> bool:
    method = message.get("method")
    request_id = message.get("id")

    if request_id is None:
        if method == "exit":
            return False
        return True

    if method == "initialize":
        ensure_server_running()
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
    while True:
        message = read_message()
        if message is None:
            break
        if not handle_message(message):
            break


if __name__ == "__main__":
    main()
