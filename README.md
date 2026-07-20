# Background STT Detector for Zed


This Zed extension runs the local background service that controls Agent dictation with voice phrases. It is separate from `realtime-stt-zed`. This background service detects commands, while the realtime service transcribes the prompt itself.

## How commands are determined

1. The Zed fork sends dictation **start word** and **stop word** as a `phrase` query parameters to `ws://127.0.0.1:8764/ws/stream`.
2. Zed streams microphone audio chunks. Silero VAD segments speech and faster-whisper transcribes each segment, using the requested phrases as its initial prompt.
3. The server lowercases and tokenises the transcript, then compares consecutive words with each phrase. Every word must reach a `SequenceMatcher` similarity of at least `0.75`.
4. The server returns positional `found` flags for both partial and final transcripts. Zed maps only `[true, false]` to Start and `[false, true]` to Stop. If transcripts contain both start and stop words or neither - they are ignored.

The values `start zed`, `stop zed`, `hey zed`, and `wake up` in `settings.example.yaml` are only a fallback Whisper prompt. The Zed client is responsible for supplying the marker words.

The extension's LSP and MCP stubs can start the local server. The MCP launcher additionally watches the Zed process and stops the server when it exits. The server exposes `/health`, `/status`, `/model/select`, and `/ws/stream`. See [`server/README.md`](server/README.md) for its standalone API and test client.
