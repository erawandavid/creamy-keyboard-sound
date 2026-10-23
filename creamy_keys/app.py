"""Turns key presses into creamy sounds."""

from __future__ import annotations

import sys
import time
import traceback
import zlib
from typing import Callable, Collection, Hashable, Optional, Tuple

import numpy as np

from .bank import SoundBank, resample
from .keys import KeyTracker, classify, normalise
from .mixer import Mixer

# Codes of the M key for the Ctrl+Alt+M mute shortcut. Windows and macOS
# report the physical key; X11 reports the symbol, which is m or M.
M_KEY_CODES = {"win32": {0x4D}, "darwin": {0x2E}}.get(sys.platform, {0x6D, 0x4D})

MUTE_SHORTCUT = "Control+Option+M" if sys.platform == "darwin" else "Ctrl+Alt+M"

# Windows and macOS key codes name the physical key, so they stay the same
# with Shift or Ctrl held. X11 reports a symbol that changes with Shift (A on
# press, a on release if Shift goes first), so the lower-case character is
# steadier there.
PHYSICAL_KEY_CODES = sys.platform in ("win32", "darwin")


class CreamyKeyboard:
    """Decides what to play for each key press and release.

    Keys are passed in as ``key``, anything that identifies the physical key
    (the same value on press and release), and ``name``, such as ``"a"``,
    ``"space"`` or ``"shift_r"``.
    """

    def __init__(
        self,
        bank: SoundBank,
        mixer: Mixer,
        *,
        pitch: float = 1.0,
        release_sounds: bool = True,
        on_mute: Optional[Callable[[bool], None]] = None,
        mute_key_codes: Collection[Hashable] = M_KEY_CODES,
        clock: Callable[[], float] = time.monotonic,
        seed: Optional[int] = None,
    ):
        self.bank = bank
        self.mixer = mixer
        self.pitch = pitch
        self.release_sounds = release_sounds
        self.muted = False
        self._on_mute = on_mute
        self._mute_key_codes = mute_key_codes
        self._tracker = KeyTracker(clock)
        self._modifiers = set()
        self._rng = np.random.default_rng(seed)

    def press(self, key: Hashable, name: str) -> None:
        name = normalise(name)
        if name in ("ctrl", "alt"):
            self._modifiers.add(name)
        if not self._tracker.press(key):
            return  # auto-repeat from holding the key down
        if {"ctrl", "alt"} <= self._modifiers and (name == "m" or key in self._mute_key_codes):
            self.toggle_mute()
        elif not self.muted:
            self._play(self.bank.press(classify(name), self._rng), key)

    def release(self, key: Hashable, name: str) -> None:
        name = normalise(name)
        self._modifiers.discard(name)
        if not self._tracker.release(key) or self.muted or not self.release_sounds:
            return
        sound = self.bank.release(classify(name), self._rng)
        if sound is not None:
            self._play(sound, key)

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        if self._on_mute:
            self._on_mute(self.muted)

    def _play(self, sound: np.ndarray, key: Hashable) -> None:
        rate = self.pitch * key_pitch(key) * self._rng.uniform(0.985, 1.015)
        self.mixer.play(resample(sound, rate) * self._rng.uniform(0.85, 1.0))


def key_pitch(key: Hashable) -> float:
    """A stable pitch for each key, within 3%, as no two keys on a real board sound the same."""
    spread = zlib.crc32(str(key).encode()) % 1001 / 1000 - 0.5
    return 1 + 0.06 * spread


def describe(key) -> Tuple[Hashable, str]:
    """Turn a pynput key into the ``(key, name)`` pair CreamyKeyboard takes."""
    from pynput.keyboard import Key

    if isinstance(key, Key):
        return key, key.name
    char = getattr(key, "char", None) or ""
    vk = getattr(key, "vk", None)
    if vk is not None and (PHYSICAL_KEY_CODES or not char):
        return vk, char
    return char.lower() or key, char


def listen(keyboard: CreamyKeyboard) -> None:
    """Play sounds for keys pressed anywhere on the computer, until Ctrl+C."""
    from pynput import keyboard as pynput_keyboard

    def safely(handler):
        def callback(key):
            if key is None:  # some platforms report unknown keys as None
                return
            try:
                handler(*describe(key))
            except Exception:  # an exception would stop the listener for good
                traceback.print_exc()

        return callback

    listener = pynput_keyboard.Listener(
        on_press=safely(keyboard.press), on_release=safely(keyboard.release)
    )
    with listener:
        if sys.platform == "darwin" and not getattr(listener, "IS_TRUSTED", True):
            print(
                "\nmacOS is blocking keyboard access, so you will not hear anything yet.\n"
                "Open System Settings > Privacy & Security, allow your Terminal app under\n"
                "both 'Accessibility' and 'Input Monitoring', then start this again.\n"
            )
        while listener.is_alive():
            listener.join(0.5)


def demo(keyboard: CreamyKeyboard, text: str = "creamy keys sound so good\n") -> None:
    """Type ``text`` on a virtual keyboard, to hear the sounds without any setup."""
    rng = np.random.default_rng()
    for char in text:
        key, name = f"demo-{char}", "enter" if char == "\n" else char
        keyboard.press(key, name)
        time.sleep(rng.uniform(0.04, 0.08))
        keyboard.release(key, name)
        time.sleep(rng.uniform(0.05, 0.14) + (0.25 if char in " \n" else 0))
    time.sleep(0.4)
