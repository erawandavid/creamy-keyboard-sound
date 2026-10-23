import numpy as np
import pytest

from creamy_keys.app import CreamyKeyboard, key_pitch
from creamy_keys.bank import SoundBank

SR = 44100
M = 0x4D


class FakeMixer:
    def __init__(self):
        self.played = []

    def play(self, samples):
        self.played.append(samples)


def make_keyboard(**kwargs):
    # Each category gets a different length so tests can tell them apart.
    bank = SoundBank(
        presses={
            "key": [np.full(1000, 0.5, np.float32)],
            "wide": [np.full(2000, 0.5, np.float32)],
            "space": [np.full(3000, 0.5, np.float32)],
        },
        releases={"key": [np.full(500, 0.1, np.float32)]},
        samplerate=SR,
    )
    mixer = FakeMixer()
    keyboard = CreamyKeyboard(bank, mixer, mute_key_codes={M}, seed=0, **kwargs)
    return keyboard, mixer


def test_press_and_release_play_sounds():
    keyboard, mixer = make_keyboard()
    keyboard.press(65, "a")
    keyboard.release(65, "a")
    assert len(mixer.played) == 2
    press, release = mixer.played
    assert np.max(press) > np.max(release)


def test_long_keys_get_their_own_sounds():
    keyboard, mixer = make_keyboard()
    keyboard.press("space", "space")
    keyboard.press("enter", "enter")
    keyboard.press(65, "a")
    lengths = [len(s) for s in mixer.played]
    assert lengths == sorted(lengths, reverse=True)
    assert lengths[0] == pytest.approx(3000, rel=0.05)


def test_holding_a_key_plays_once():
    keyboard, mixer = make_keyboard(release_sounds=False)
    for _ in range(10):
        keyboard.press(65, "a")
    keyboard.release(65, "a")
    assert len(mixer.played) == 1


def test_no_release_sounds_option():
    keyboard, mixer = make_keyboard(release_sounds=False)
    keyboard.press(65, "a")
    keyboard.release(65, "a")
    assert len(mixer.played) == 1


def test_ctrl_alt_m_toggles_mute():
    changes = []
    keyboard, mixer = make_keyboard(release_sounds=False, on_mute=changes.append)

    def chord():
        keyboard.press("ctrl", "ctrl_l")
        keyboard.press("alt", "alt_l")
        keyboard.press(M, "")
        for key, name in ((M, ""), ("alt", "alt_l"), ("ctrl", "ctrl_l")):
            keyboard.release(key, name)

    chord()
    assert keyboard.muted and changes == [True]
    played = len(mixer.played)
    keyboard.press(65, "a")
    assert len(mixer.played) == played

    chord()
    assert not keyboard.muted and changes == [True, False]
    keyboard.press(66, "b")
    assert len(mixer.played) == played + 1


def test_m_without_both_modifiers_does_not_mute():
    keyboard, mixer = make_keyboard()
    keyboard.press(M, "m")
    keyboard.release(M, "m")
    keyboard.press("ctrl", "ctrl")
    keyboard.press(M, "m")
    assert not keyboard.muted
    assert len(mixer.played) == 4


def test_pitch_changes_playback_speed():
    deep, deep_mixer = make_keyboard(pitch=0.5)
    normal, normal_mixer = make_keyboard()
    deep.press(65, "a")
    normal.press(65, "a")
    assert len(deep_mixer.played[0]) == pytest.approx(2 * len(normal_mixer.played[0]), rel=0.05)


def test_each_key_has_its_own_stable_pitch():
    pitches = {key: key_pitch(key) for key in range(32, 128)}
    assert all(0.97 <= p <= 1.03 for p in pitches.values())
    assert len(set(pitches.values())) > 50
    assert key_pitch(65) == pitches[65]
