"""Low-latency playback: overlapping key sounds mixed straight into the sound card."""

from __future__ import annotations

import sys
from collections import deque
from typing import Deque, List, Optional, Union

import numpy as np

Device = Optional[Union[int, str]]


class Mixer:
    """Mixes any number of overlapping sounds.

    ``play`` may be called from any thread; ``render`` is called by the audio
    callback. A deque hands sounds over without locks, so a burst of typing
    never stalls the audio.
    """

    def __init__(self, volume: float = 1.0, max_voices: int = 32):
        self.volume = volume
        self.max_voices = max_voices
        self._incoming: Deque[np.ndarray] = deque()
        self._voices: List[List] = []  # [samples, position]

    def play(self, samples: np.ndarray) -> None:
        self._incoming.append(samples)

    def render(self, frames: int) -> np.ndarray:
        while self._incoming:
            self._voices.append([self._incoming.popleft(), 0])
        del self._voices[: -self.max_voices]

        out = np.zeros(frames, np.float32)
        playing = []
        for voice in self._voices:
            samples, position = voice
            chunk = samples[position : position + frames]
            out[: len(chunk)] += chunk
            voice[1] = position + len(chunk)
            if voice[1] < len(samples):
                playing.append(voice)
        self._voices = playing

        out *= self.volume
        return np.tanh(out, out=out)  # soft limiter for fast typing


class AudioOutput:
    """Streams a Mixer to a sound card through PortAudio."""

    def __init__(self, mixer: Mixer, device: Device = None):
        import sounddevice as sd

        self._sd = sd
        self.mixer = mixer
        self.stream = None
        candidates = [device] if device is not None else [_fast_default_output(sd), None]
        errors = []
        for candidate in dict.fromkeys(candidates):
            try:
                self.stream = self._open(candidate)
                break
            except Exception as e:  # PortAudio reports problems as many types
                errors.append(f"{candidate}: {e}")
        if self.stream is None:
            raise RuntimeError("could not open an audio output: " + "; ".join(errors))
        self.samplerate = int(self.stream.samplerate)
        self.device_name = sd.query_devices(self.stream.device)["name"]

    def _open(self, device: Device):
        info = self._sd.query_devices(device, "output")
        channels = min(2, info["max_output_channels"])
        return self._sd.OutputStream(
            device=device,
            samplerate=info["default_samplerate"],
            channels=channels,
            dtype="float32",
            latency="low",
            callback=self._callback,
        )

    def _callback(self, outdata, frames, time, status) -> None:
        outdata[:] = self.mixer.render(frames)[:, None]

    def start(self) -> None:
        self.stream.start()

    def close(self) -> None:
        self.stream.stop()
        self.stream.close()


def _fast_default_output(sd) -> Optional[int]:
    """On Windows the default (MME) output adds ~100 ms of lag; WASAPI doesn't."""
    if sys.platform != "win32":
        return None
    for api in sd.query_hostapis():
        if "WASAPI" in api["name"] and api["default_output_device"] >= 0:
            return api["default_output_device"]
    return None


def list_devices() -> str:
    import sounddevice as sd

    return str(sd.query_devices())


def parse_device(text: Optional[str]) -> Device:
    """``--device 3`` means device number 3, anything else is a name."""
    if text is None:
        return None
    return int(text) if text.isdigit() else text
