import numpy as np
import torch
import time
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class AudioEvent:
    type: str  # "speech_start", "partial_ready", "speech_end"
    audio: Optional[np.ndarray] = None


class AudioProcessor:
    def __init__(
            self,
            sample_rate: int = 16000,
            vad_threshold: float = 0.5,
            partial_interval_s: float = 1.0,
            max_buffer_s: float = 30.0,
    ):
        self.sample_rate = sample_rate
        self.vad_threshold = vad_threshold
        self.partial_interval_s = partial_interval_s
        self.max_buffer_samples = int(max_buffer_s * sample_rate)
        self.vad_chunk_samples = 512 if sample_rate == 16000 else 256
        # How many consecutive silent VAD frames before we declare speech ended.
        # 600 ms gives enough headroom for natural pauses between words/phrases.
        self._silence_threshold_frames = max(1, int(0.6 * sample_rate / self.vad_chunk_samples))

        # Load Silero VAD
        # Uses CPU, lightweight
        self.vad_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad',
                                               force_reload=False, trust_repo=True)
        self.vad_model.eval()
        self.get_speech_timestamps = utils[0]

        self.reset()

    def reset(self):
        self._buffer = np.array([], dtype=np.float32)
        self._vad_pending = np.array([], dtype=np.float32)
        self._is_speaking = False
        self._last_partial_time = 0.0
        self._silence_frames = 0  # consecutive silent frames since last speech
        self.vad_model.reset_states()

    def feed(self, raw_bytes: bytes) -> List[AudioEvent]:
        """
        Feeds raw 16-bit PCM mono audio bytes.
        Returns a list of AudioEvents triggered by this chunk.
        """
        # Convert bytes to float32 numpy array
        # 16-bit PCM -> int16
        audio_int16 = np.frombuffer(raw_bytes, dtype=np.int16)
        # Normalize to [-1.0, 1.0] float32
        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        events = []
        self._vad_pending = np.concatenate((self._vad_pending, audio_float32))

        while len(self._vad_pending) >= self.vad_chunk_samples:
            vad_frame = self._vad_pending[:self.vad_chunk_samples]
            self._vad_pending = self._vad_pending[self.vad_chunk_samples:]
            events.extend(self._feed_vad_frame(vad_frame))

        return events

    def _feed_vad_frame(self, audio_frame: np.ndarray) -> List[AudioEvent]:
        # Silero streaming VAD expects exactly 512 samples at 16 kHz.
        audio_tensor = torch.from_numpy(audio_frame)
        speech_prob = self.vad_model(audio_tensor, self.sample_rate).item()

        is_speech_now = speech_prob >= self.vad_threshold
        events = []

        if is_speech_now and not self._is_speaking:
            self._is_speaking = True
            self._silence_frames = 0
            events.append(AudioEvent(type="speech_start"))
            self._buffer = audio_frame.copy()
            self._last_partial_time = time.time()

        elif self._is_speaking:
            # Always accumulate (including silence frames during hangover period)
            self._buffer = np.concatenate((self._buffer, audio_frame))

            # Force a final segment if the buffer exceeds the maximum duration
            if len(self._buffer) >= self.max_buffer_samples:
                events.append(AudioEvent(type="speech_end", audio=self._buffer.copy()))
                self._is_speaking = False
                self._buffer = np.array([], dtype=np.float32)
                self.vad_model.reset_states()
                self._silence_frames = 0

            elif not is_speech_now:
                # Silence frame: increment hangover counter but don't end yet.
                # Only fire speech_end after sustained silence to avoid cutting
                # mid-utterance on natural micro-pauses.
                self._silence_frames += 1
                if self._silence_frames >= self._silence_threshold_frames:
                    events.append(AudioEvent(type="speech_end", audio=self._buffer.copy()))
                    self._is_speaking = False
                    self._buffer = np.array([], dtype=np.float32)
                    self.vad_model.reset_states()
                    self._silence_frames = 0

            else:
                # Active speech: reset silence counter and check for partials
                self._silence_frames = 0
                current_time = time.time()
                if current_time - self._last_partial_time >= self.partial_interval_s:
                    self._last_partial_time = current_time
                    events.append(AudioEvent(type="partial_ready", audio=self._buffer.copy()))

        return events
