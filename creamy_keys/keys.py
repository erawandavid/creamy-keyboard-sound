"""Which sound a key gets, and telling real presses apart from auto-repeat."""

from __future__ import annotations

import time
from typing import Callable, Dict, Hashable, Tuple

# Long keys sit on stabilisers and sound deeper than the alphas.
WIDE_KEYS = {"enter", "backspace", "shift", "tab", "caps_lock"}

# Control characters such as "\r" are not mapped: Windows reports Ctrl+M as
# "\r", and that should still sound like an ordinary key.
CHAR_NAMES = {" ": "space"}

# Holding a key makes the OS send repeated presses. The first repeat comes
# after the "repeat delay" (at most ~2 s on any OS), the rest follow quickly,
# so a press that arrives later than this after the last one is a new press.
REPEAT_WINDOW = 2.0


def normalise(name: str) -> str:
    """Map a key name like ``shift_r`` or ``" "`` to a plain name like ``shift``."""
    name = CHAR_NAMES.get(name, name).lower()
    for suffix in ("_l", "_r", "_gr"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def classify(name: str) -> Tuple[str, ...]:
    """Sound categories to try for a key, most specific first.

    Every chain ends in ``"key"``, the sound all sound banks must provide.
    """
    name = normalise(name)
    if len(name) <= 1:
        return ("key",)
    if name == "space":
        return ("space", "key")
    if name in WIDE_KEYS:
        return (name, "wide", "key")
    return (name, "key")


class KeyTracker:
    """Remembers which keys are down so auto-repeat stays silent."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._down: Dict[Hashable, float] = {}

    def press(self, key: Hashable) -> bool:
        """Record a press; True if it is a real keystroke, False if auto-repeat."""
        now = self._clock()
        last = self._down.get(key)
        self._down[key] = now
        # A key whose release we missed must not stay silent forever.
        return last is None or now - last > REPEAT_WINDOW

    def release(self, key: Hashable) -> bool:
        """Record a release; True if the key was down."""
        return self._down.pop(key, None) is not None
