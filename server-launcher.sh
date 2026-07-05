#!/usr/bin/env bash
# Runs in background: installs deps if needed, then starts the STT server.
# Zed gets "sleep infinity" as the LSP process while the real server runs alongside.
# Not currently invoked directly (lsp-stub.py starts the server itself via subprocess),
# kept as a manual entry point for local testing outside of Zed.

SERVER_DIR="$(dirname "$0")/server"
VENV_DIR="${VENV_DIR:-${SERVER_DIR}/.venv}"
SETTINGS_PATH="${SETTINGS_PATH:-${SERVER_DIR}/settings.yaml}"

export VENV_DIR
export SETTINGS_PATH

# Install + start the real server in background
bash "${SERVER_DIR}/setup.sh" &

# Keep this process alive so Zed doesn't kill the language server slot
wait
