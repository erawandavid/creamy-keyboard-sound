import numpy as np
import pytest

from creamy_keys.synth import PHONE_PROFILES, PRESS_PROFILES, release_profile, render

SR = 44100


def spectrum(x):
    power = np.abs(np.fft.rfft(x, 1 << 15)) ** 2
    freqs = np.fft.rfftfreq(1 << 15, 1 / SR)
    return freqs, power / power.sum()


def centroid(x):
    freqs, power = spectrum(x)
    return float((freqs * power).sum())


@pytest.mark.parametrize("category", sorted(PRESS_PROFILES))
def test_sounds_are_clean(category):
    profile = PRESS_PROFILES[category]
    x = render(profile, SR, np.random.default_rng(0))
    assert x.dtype == np.float32
    assert len(x) == int(profile.length * SR)
    assert np.all(np.isfinite(x))
    assert np.max(np.abs(x)) == pytest.approx(profile.level, rel=1e-3)
    # Starts and ends at silence, so there are no clicks.
    assert abs(x[0]) < 1e-3
    assert abs(x[-1]) < 1e-3


@pytest.mark.parametrize("category", sorted(PRESS_PROFILES))
def test_sounds_are_creamy_not_clacky(category):
    x = render(PRESS_PROFILES[category], SR, np.random.default_rng(1))
    freqs, power = spectrum(x)
    assert centroid(x) < 1000
    assert power[freqs > 3200].sum() < 0.04
    # ...but not a sub-bass thud that laptop speakers cannot play.
    assert power[freqs > 100].sum() > 0.9


def test_bigger_keys_sound_deeper():
    rng = np.random.default_rng(2)
    pitch = {
        name: np.median([centroid(render(p, SR, rng)) for _ in range(15)])
        for name, p in PRESS_PROFILES.items()
    }
    assert pitch["key"] > pitch["wide"] > pitch["space"]


def test_release_is_quieter_and_shorter():
    for profile in PRESS_PROFILES.values():
        up = release_profile(profile)
        assert up.level < profile.level / 2
        assert up.length < profile.length
        assert up.body_hz > profile.body_hz


def test_variants_differ_but_seeds_repeat():
    profile = PRESS_PROFILES["key"]
    a = render(profile, SR, np.random.default_rng(5))
    b = render(profile, SR, np.random.default_rng(6))
    again = render(profile, SR, np.random.default_rng(5))
    assert not np.allclose(a, b)
    assert np.array_equal(a, again)


def test_other_samplerates():
    x = render(PRESS_PROFILES["key"], 48000, np.random.default_rng(0))
    assert len(x) == int(PRESS_PROFILES["key"].length * 48000)
    assert np.all(np.isfinite(x))


def fade_time(x, level):
    """Milliseconds from the loudest point until the sound stays below ``level`` of it."""
    a = np.abs(x)
    start = int(np.argmax(a))
    tail = np.maximum.accumulate(a[::-1])[::-1][start:]
    return np.argmax(tail < level * a[start]) / SR * 1000


@pytest.mark.parametrize("category", sorted(PHONE_PROFILES))
def test_phone_taps_are_short_crisp_ticks(category):
    x = render(PHONE_PROFILES[category], SR, np.random.default_rng(3))
    assert np.all(np.isfinite(x))
    assert fade_time(x, 0.1) < 6
    assert fade_time(x, 0.03) < 12


def test_phone_letters_tick_highest_and_delete_lowest():
    pitch = {name: centroid(render(p, SR, np.random.default_rng(4))) for name, p in PHONE_PROFILES.items()}
    assert pitch["key"] > pitch["wide"] > pitch["backspace"]
    assert pitch["space"] == pytest.approx(pitch["wide"], rel=0.1)
    assert 1500 < pitch["key"] < 2300
