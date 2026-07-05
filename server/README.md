# background-realtime-stt-server

Local FastAPI + WebSocket real-time STT server, streaming 16kHz mono PCM16 audio through Silero VAD segmentation into a single `whisper_tiny` (faster-whisper) engine. Adapted from [ZolotarevAlexandr/realtime_stt](https://github.com/ZolotarevAlexandr/realtime_stt), trimmed to the one model that won the accuracy benchmark for this use case (see `../../background_voice/BENCHMARK.md`).

## Run standalone (without Zed)

```bash
./run-local.sh
```

Creates `.venv`, installs deps from `pyproject.toml`, copies `settings.example.yaml` to `settings.yaml` if missing, starts the server on `127.0.0.1:8765`.

## Test

```bash
.venv/bin/python -m tests.tester --file test.wav --language en
# or from the mic (needs pyaudio + portaudio):
.venv/bin/python -m tests.tester --language ru
```

## API

- `GET /health` — liveness check.
- `GET /status` — currently loaded model.
- `POST /model/select` — `{"model_name": "whisper_tiny", "language": "ru"}`.
- `WS /ws/stream` — send raw 16kHz mono PCM16 chunks, receive `{"type": "partial"|"final", "text": ...}` events.
