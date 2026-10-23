"""Synthesised "creamy" mechanical keyboard sounds.

A creamy board (lubed linear switches, a foam-filled case, thick PBT caps)
sounds deep, round and muted: a soft attack, a low "thock" from the case and
almost none of the bright clack of a stock keyboard. Every sound here is made
from the same few ingredients:

* the bottom-out tap: a short burst of noise, heavily low-passed so it is
  smooth instead of scratchy;
* the body: a handful of damped resonant modes whose pitch drops a little
  right after impact, which is what makes it "thock" rather than "beep";
* gentle saturation, which adds warmth and lets the deep notes come through
  even on small laptop speakers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class Profile:
    """Recipe for one family of key sounds."""

    body_hz: float  # pitch of the low thock
    body_decay: float  # seconds for the thock to fade to 1/e
    tap_cutoff: float  # low-pass on the bottom-out tap; lower is creamier
    tap_level: float
    length: float  # seconds
    level: float  # peak level of the finished sound
    second_hit: float = 0.0  # long keys bottom out at both ends, slightly apart
    # Resonant modes of case and keycap as (pitch ratio, level, decay ratio).
    # The higher ones are the muted "pop" that gives a press its definition.
    modes: Tuple[Tuple[float, float, float], ...] = (
        (1.0, 1.0, 1.0),
        (1.59, 0.75, 0.7),
        (2.71, 0.6, 0.45),
        (4.3, 0.65, 0.35),
    )


PRESS_PROFILES = {
    "key": Profile(
        body_hz=250, body_decay=0.020, tap_cutoff=3000, tap_level=0.9,
        length=0.12, level=0.50,
    ),
    "wide": Profile(
        body_hz=185, body_decay=0.026, tap_cutoff=2600, tap_level=0.9,
        length=0.16, level=0.56, second_hit=0.30,
    ),
    "space": Profile(
        body_hz=140, body_decay=0.034, tap_cutoff=2200, tap_level=1.0,
        length=0.22, level=0.62, second_hit=0.45,
    ),
}


def release_profile(press: Profile) -> Profile:
    """The upstroke: the keycap returning to the top, quieter and lighter."""
    return replace(
        press,
        body_hz=press.body_hz * 1.4,
        body_decay=press.body_decay * 0.55,
        tap_cutoff=press.tap_cutoff * 0.8,
        tap_level=press.tap_level * 0.7,
        length=press.length * 0.6,
        level=press.level * 0.3,
        second_hit=0.0,
    )


def render(profile: Profile, samplerate: int, rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """Render one key sound as mono float32 samples.

    ``rng`` adds the small random differences that keep repeated presses
    from sounding robotic.
    """
    rng = rng if rng is not None else np.random.default_rng()

    def vary(spread: float) -> float:
        return 1.0 + rng.uniform(-spread, spread)

    n = int(profile.length * samplerate)
    t = np.arange(n) / samplerate
    f0 = profile.body_hz * vary(0.04)
    decay = profile.body_decay * vary(0.12)

    glide = 1.0 + 0.12 * np.exp(-t / 0.004)
    phase = 2 * np.pi * np.cumsum(f0 * glide) / samplerate
    body = np.zeros(n)
    for i, (ratio, level, decay_ratio) in enumerate(profile.modes):
        # The main thock starts from rest; the overtones vary from press to press.
        start = rng.uniform(0, 2 * np.pi) if i else 0.0
        body += (
            level * vary(0.15)
            * np.sin(ratio * vary(0.02) * phase + start)
            * np.exp(-t / (decay * decay_ratio))
        )

    tap_n = min(n, int(0.03 * samplerate))
    tap = rng.standard_normal(tap_n) * np.exp(-np.arange(tap_n) / samplerate / 0.005)
    cutoff = profile.tap_cutoff * vary(0.1)
    tap = _filter(_filter(tap, "low", cutoff, samplerate), "low", cutoff, samplerate)
    # Below the body there is nothing to hear on a laptop, only a dull thud.
    tap = _filter(tap, "high", profile.body_hz, samplerate)
    tap *= profile.tap_level * vary(0.15) * _peak(body) / _peak(tap)
    body[:tap_n] += tap
    if profile.second_hit:
        offset = int(rng.uniform(0.004, 0.009) * samplerate)
        end = min(n, offset + tap_n)
        body[offset:end] += profile.second_hit * vary(0.2) * tap[: end - offset]

    # A rounded attack is a big part of what separates creamy from clicky.
    attack = int(0.0008 * samplerate)
    body[:attack] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, attack))
    fade = int(0.015 * samplerate)
    body[-fade:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fade))

    drive = 1.6
    sound = np.tanh(drive * body / _peak(body)) / math.tanh(drive)
    return (profile.level * sound / _peak(sound)).astype(np.float32)


def _peak(x: np.ndarray) -> float:
    return float(np.max(np.abs(x))) or 1.0


def _filter(x: np.ndarray, kind: str, cutoff: float, samplerate: int, q: float = 0.707) -> np.ndarray:
    """Second-order (RBJ biquad) ``"low"``- or ``"high"``-pass filter."""
    w = 2 * math.pi * min(cutoff, 0.45 * samplerate) / samplerate
    alpha = math.sin(w) / (2 * q)
    cos_w = math.cos(w)
    a0 = 1 + alpha
    edge = 1 - cos_w if kind == "low" else 1 + cos_w
    b0 = b2 = edge / 2 / a0
    b1 = (edge if kind == "low" else -edge) / a0
    a1 = -2 * cos_w / a0
    a2 = (1 - alpha) / a0

    out = []
    x1 = x2 = y1 = y2 = 0.0
    for xi in x.tolist():
        yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, xi, y1, yi
        out.append(yi)
    return np.array(out)
