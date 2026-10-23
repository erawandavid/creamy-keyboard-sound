"""Sets of ready-to-play key sounds: synthesised, or loaded from WAV files."""

from __future__ import annotations

import re
import wave
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

from .synth import PRESS_PROFILES, release_profile, render

# Other file names people are likely to use for the same keys.
ALIASES = {
    "keys": "key",
    "default": "key",
    "spacebar": "space",
    "return": "enter",
    "caps": "caps_lock",
    "capslock": "caps_lock",
}

Sounds = Dict[str, List[np.ndarray]]


class SoundBank:
    """Press and release sounds per category, a few variants each."""

    def __init__(self, presses: Sounds, releases: Sounds, samplerate: int):
        if not presses.get("key"):
            raise ValueError('a sound bank needs at least one "key" sound')
        self.presses = presses
        self.releases = releases
        self.samplerate = samplerate

    def press(self, categories: Sequence[str], rng: np.random.Generator) -> np.ndarray:
        """A press sound for the first category in ``categories`` the bank has."""
        sound = self._pick(self.presses, categories, rng)
        assert sound is not None  # every chain ends in "key"
        return sound

    def release(self, categories: Sequence[str], rng: np.random.Generator) -> Optional[np.ndarray]:
        """A release sound, or None if the bank has none for these keys."""
        return self._pick(self.releases, categories, rng)

    @staticmethod
    def _pick(sounds: Sounds, categories: Sequence[str], rng: np.random.Generator):
        for category in categories:
            variants = sounds.get(category)
            if variants:
                return variants[rng.integers(len(variants))]
        return None


def synthesize(samplerate: int, variants: int = 8, seed: Optional[int] = None) -> SoundBank:
    """The built-in creamy sound set."""
    rng = np.random.default_rng(seed)
    presses: Sounds = {}
    releases: Sounds = {}
    for category, profile in PRESS_PROFILES.items():
        up = release_profile(profile)
        presses[category] = [render(profile, samplerate, rng) for _ in range(variants)]
        releases[category] = [render(up, samplerate, rng) for _ in range(variants)]
    return SoundBank(presses, releases, samplerate)


def load_pack(folder: Path, samplerate: int) -> SoundBank:
    """Load a folder of WAV files named after the keys they are for.

    ``key.wav`` (or ``key1.wav``, ``key2.wav``, ...) is used for every key that
    has no file of its own; ``space.wav``, ``enter.wav``, ``wide.wav`` (all long
    keys) etc. are optional, and so are release sounds such as
    ``release.wav`` or ``space-release.wav``.
    """
    folder = Path(folder)
    presses: Sounds = defaultdict(list)
    releases: Sounds = defaultdict(list)
    for path in sorted(folder.glob("*.[wW][aA][vV]")):
        stem = re.sub(r"[-_ ]*\d*$", "", path.stem.lower())
        target = presses
        if stem.endswith("release"):
            stem = stem[: -len("release")].rstrip("-_ ") or "key"
            target = releases
        target[ALIASES.get(stem, stem)].append(read_wav(path, samplerate))
    if not presses.get("key"):
        raise ValueError(f'{folder} needs a "key.wav" (the sound used for most keys)')
    return SoundBank(dict(presses), dict(releases), samplerate)


def read_wav(path: Path, samplerate: int) -> np.ndarray:
    """Read a PCM WAV file as mono float32 at ``samplerate``."""
    try:
        with wave.open(str(path), "rb") as f:
            width = f.getsampwidth()
            channels = f.getnchannels()
            rate = f.getframerate()
            raw = f.readframes(f.getnframes())
    except (wave.Error, EOFError) as e:
        raise ValueError(f"cannot read {path} ({e}); save it as a 16-bit PCM WAV") from e

    if width == 1:
        data = (np.frombuffer(raw, np.uint8).astype(np.float32) - 128) / 128
    elif width == 2:
        data = np.frombuffer(raw, "<i2").astype(np.float32) / 2**15
    elif width == 3:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
        ints = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        data = (np.where(ints >= 2**23, ints - 2**24, ints) / 2**23).astype(np.float32)
    elif width == 4:
        data = (np.frombuffer(raw, "<i4") / 2**31).astype(np.float32)
    else:
        raise ValueError(f"{path}: unsupported sample width of {width} bytes")

    data = data.reshape(-1, channels).mean(axis=1)
    if rate != samplerate and len(data) > 1:
        data = resample(data, rate / samplerate)
    return data.astype(np.float32)


def write_wav(path: Path, samples: np.ndarray, samplerate: int) -> None:
    """Write mono float samples as a 16-bit PCM WAV file."""
    ints = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(samplerate)
        f.writeframes(ints.tobytes())


def resample(samples: np.ndarray, rate: float) -> np.ndarray:
    """Play ``samples`` ``rate`` times faster: above 1 is higher and shorter."""
    positions = np.arange(0, len(samples) - 1, rate)
    return np.interp(positions, np.arange(len(samples)), samples).astype(np.float32)
