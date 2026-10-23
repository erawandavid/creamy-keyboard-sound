import wave

import numpy as np
import pytest

from creamy_keys.__main__ import export
from creamy_keys.bank import SoundBank, load_pack, read_wav, resample, synthesize, write_wav

SR = 44100


def tone(seconds=0.05, samplerate=SR, level=0.5):
    t = np.arange(int(seconds * samplerate)) / samplerate
    return (level * np.sin(2 * np.pi * 440 * t)).astype(np.float32)


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
    for name in ["key1", "Key_2", "spacebar", "Return", "release", "space-release", "notes"]:
        write_wav(tmp_path / f"{name}.wav", tone(), SR)
    (tmp_path / "readme.txt").write_text("ignored")

    bank = load_pack(tmp_path, SR)
    assert len(bank.presses["key"]) == 2
    assert set(bank.presses) == {"key", "space", "enter", "notes"}
    assert set(bank.releases) == {"key", "space"}


def test_load_pack_needs_key_wav(tmp_path):
    write_wav(tmp_path / "space.wav", tone(), SR)
    with pytest.raises(ValueError, match="key.wav"):
        load_pack(tmp_path, SR)


def test_exported_sounds_load_back_as_a_pack(tmp_path):
    export(tmp_path)
    bank = load_pack(tmp_path, SR)
    built_in = synthesize(SR, seed=0)
    for sounds, original in ((bank.presses, built_in.presses), (bank.releases, built_in.releases)):
        assert {k: len(v) for k, v in sounds.items()} == {k: len(v) for k, v in original.items()}


def test_resample():
    x = tone()
    assert len(resample(x, 2.0)) == pytest.approx(len(x) / 2, abs=1)
    assert len(resample(x, 0.5)) == pytest.approx(len(x) * 2, abs=2)
    assert np.allclose(resample(x, 1.0), x[:-1])
