import wave

import numpy as np
import pytest

from creamy_keys.bank import (
    BUILTIN_PACK, LOUDNESS, MAX_PEAK, SoundBank, load_pack, read_wav, resample, synthesize, tidy,
)
from creamy_keys.keys import classify

SR = 44100


def tone(seconds=0.05, samplerate=SR, level=0.5):
    t = np.arange(int(seconds * samplerate)) / samplerate
    return (level * np.sin(2 * np.pi * 440 * t)).astype(np.float32)


def write_wav(path, samples, samplerate):
    ints = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(samplerate)
        f.writeframes(ints.tobytes())


def loudness(x):
    window = min(len(x), int(0.02 * SR))
    return np.sqrt(np.convolve(x**2, np.ones(window) / window, "valid").max())


def test_builtin_pack_has_a_sound_for_every_letter():
    bank = load_pack(BUILTIN_PACK, SR)
    for letter in "abcdefghijklmnopqrstuvwxyz[]":
        assert len(bank.presses[letter]) == 1
    for key in ("space", "enter", "backspace", "shift", "tab", "caps_lock"):
        assert bank.presses[key]
    # Keys without a recording borrow one of the letters'.
    assert len(bank.presses["key"]) == 28
    rng = np.random.default_rng(0)
    assert bank.press(classify("a"), rng) is bank.presses["a"][0]
    five = bank.press(classify("5"), rng)
    assert any(five is s for s in bank.presses["key"])


def test_builtin_pack_is_even_and_starts_at_the_click():
    bank = load_pack(BUILTIN_PACK, SR)
    for name, sounds in bank.presses.items():
        for s in sounds:
            assert np.max(np.abs(s)) <= MAX_PEAK + 1e-6, name
            assert loudness(s) == pytest.approx(LOUDNESS, rel=0.01) or np.max(np.abs(s)) == pytest.approx(MAX_PEAK)
            assert np.argmax(np.abs(s) > 0.1 * np.max(np.abs(s))) < 0.015 * SR, name
            assert len(s) < 0.4 * SR, name


def test_tidy_trims_silence_and_sets_loudness():
    padded = np.concatenate([np.zeros(SR // 10), tone(level=0.05), np.zeros(SR // 10)]).astype(np.float32)
    out = tidy(padded, SR)
    assert len(out) < len(tone()) + 0.012 * SR
    assert loudness(out) == pytest.approx(LOUDNESS, rel=0.01)
    assert abs(out[-1]) < 1e-3
    assert not tidy(np.zeros(100, np.float32), SR).any()


def test_tidy_never_clips_spiky_sounds():
    spike = np.zeros(SR // 10, np.float32)
    spike[100] = 0.01
    assert np.max(np.abs(tidy(spike, SR))) == pytest.approx(MAX_PEAK)


def test_synthesized_bank_has_presses_and_releases():
    bank = synthesize(SR, variants=3, seed=0)
    assert set(bank.presses) == {"key", "wide", "space"}
    assert all(len(v) == 3 for v in bank.presses.values())
    assert set(bank.releases) == set(bank.presses)


def test_bank_falls_back_along_the_chain():
    key, space = tone(level=0.1), tone(level=0.2)
    bank = SoundBank({"key": [key], "space": [space]}, {}, SR)
    rng = np.random.default_rng(0)
    assert bank.press(("space", "key"), rng) is space
    assert bank.press(("enter", "wide", "key"), rng) is key
    assert bank.release(("key",), rng) is None


def test_bank_needs_a_key_sound():
    with pytest.raises(ValueError):
        SoundBank({"space": [tone()]}, {}, SR)


def test_wav_round_trip(tmp_path):
    path = tmp_path / "key.wav"
    write_wav(path, tone(), SR)
    assert np.allclose(read_wav(path, SR), tone(), atol=1e-4)


def test_read_wav_converts_stereo_24_bit_and_samplerate(tmp_path):
    path = tmp_path / "key.wav"
    mono = tone(samplerate=22050)
    ints = (mono * (2**23 - 1)).astype("<i4")
    frames = np.repeat(ints, 2)  # stereo
    raw = b"".join(int(v).to_bytes(3, "little", signed=True) for v in frames)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(3)
        f.setframerate(22050)
        f.writeframes(raw)

    data = read_wav(path, SR)
    assert len(data) == pytest.approx(2 * len(mono), abs=2)
    assert np.max(np.abs(data)) == pytest.approx(0.5, abs=0.01)


def test_read_wav_rejects_other_files(tmp_path):
    path = tmp_path / "key.wav"
    path.write_bytes(b"not a wav file")
    with pytest.raises(ValueError, match="PCM WAV"):
        read_wav(path, SR)


def test_load_pack_names(tmp_path):
    names = ["key1", "Key_2", "spacebar", "Return", "Caps Lock", "release", "space-release", "1", "notes"]
    for name in names:
        write_wav(tmp_path / f"{name}.wav", tone(), SR)
    (tmp_path / "readme.txt").write_text("ignored")

    bank = load_pack(tmp_path, SR)
    assert len(bank.presses["key"]) == 2
    assert set(bank.presses) == {"key", "space", "enter", "caps_lock", "1", "notes"}
    assert set(bank.releases) == {"key", "space"}


def test_load_pack_needs_key_wav_or_letters(tmp_path):
    write_wav(tmp_path / "space.wav", tone(), SR)
    with pytest.raises(ValueError, match="key.wav"):
        load_pack(tmp_path, SR)


def test_resample():
    x = tone()
    assert len(resample(x, 2.0)) == pytest.approx(len(x) / 2, abs=1)
    assert len(resample(x, 0.5)) == pytest.approx(len(x) * 2, abs=2)
    assert np.allclose(resample(x, 1.0), x[:-1])
