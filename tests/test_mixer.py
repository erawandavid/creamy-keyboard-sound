import numpy as np
import pytest

from creamy_keys.mixer import Mixer, parse_device


def test_silence_when_nothing_plays():
    out = Mixer().render(256)
    assert out.dtype == np.float32
    assert not out.any()


def test_sound_is_spread_over_blocks_then_finishes():
    mixer = Mixer()
    sound = np.full(300, 0.1, np.float32)
    mixer.play(sound)
    first = mixer.render(256)
    second = mixer.render(256)
    assert np.allclose(first, np.tanh(0.1))
    assert np.allclose(second[:44], np.tanh(0.1))
    assert not second[44:].any()
    assert not mixer.render(256).any()


def test_overlapping_sounds_add_up_and_stay_in_range():
    mixer = Mixer()
    for _ in range(10):
        mixer.play(np.full(100, 0.3, np.float32))
    out = mixer.render(100)
    assert np.all(out < 1.0)
    assert out[0] == pytest.approx(np.tanh(3.0))


def test_volume():
    mixer = Mixer(volume=0.5)
    mixer.play(np.full(10, 0.2, np.float32))
    assert mixer.render(10)[0] == pytest.approx(np.tanh(0.1))


def test_oldest_voices_are_dropped():
    mixer = Mixer(max_voices=2)
    for level in (0.1, 0.2, 0.3):
        mixer.play(np.full(10, level, np.float32))
    assert mixer.render(10)[0] == pytest.approx(np.tanh(0.5))


def test_parse_device():
    assert parse_device(None) is None
    assert parse_device("3") == 3
    assert parse_device("Speakers") == "Speakers"
