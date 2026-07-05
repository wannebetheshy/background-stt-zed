#!/usr/bin/env python3
"""Minimal MCP stub that keeps Zed's context-server slot alive."""

from __future__ import annotations

import json
import sys
from typing import Any


def read_message() -> dict[str, Any] | None:
    line = sys.stdin.readline()
    if not line:
        return None

    line = line.strip()
    if not line:
        return None

    return json.loads(line)


def write_message(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None:
        return None

    if method == "initialize":
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
    while True:
        message = read_message()
        if message is None:
            break

        response = handle_request(message)
        if response is not None:
            write_message(response)


if __name__ == "__main__":
    main()
