import json
from types import SimpleNamespace

import pytest

from src import routes


class FakeWebSocket:
    def __init__(self, incoming):
        self._incoming = list(incoming)
        self.sent = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def receive(self):
        return self._incoming.pop(0)

    async def send_text(self, text):
        self.sent.append(json.loads(text))

    async def close(self):
        self.closed = True


class FakeAudioProcessor:
    def __init__(self, **kwargs):
        self._buffer = []

    def feed(self, raw_audio):
        return [
            SimpleNamespace(type="partial_ready", audio=["partial-audio"]),
            SimpleNamespace(type="speech_end", audio=["final-audio"]),
        ]


class FakeEngine:
    def __init__(self):
        self.transcribed_audio = []

    def transcribe(self, audio):
        self.transcribed_audio.append(audio)
        return [SimpleNamespace(text="final text")]


@pytest.mark.asyncio
async def test_websocket_stream_sends_only_final_transcriptions(monkeypatch):
    engine = FakeEngine()
    websocket = FakeWebSocket([
        {"bytes": b"audio"},
        {"text": json.dumps({"command": "stop"})},
    ])

    monkeypatch.setattr(routes.model_manager, "active_engine", engine)
    monkeypatch.setattr(routes, "AudioProcessor", FakeAudioProcessor)

    await routes.websocket_stream(websocket)

    assert websocket.accepted
    assert websocket.closed
    assert [message["type"] for message in websocket.sent] == ["status", "final"]
    assert websocket.sent[1] == {
        "type": "final",
        "text": "final text",
        "segment_id": 0,
        "is_final": True,
    }
    assert engine.transcribed_audio == [["final-audio"]]
