import pytest

from creamy_keys.__main__ import make_bank, parse_args

SR = 44100


def test_default_sound_is_the_cream_recordings():
    bank = make_bank(parse_args([]), SR)
    assert "a" in bank.presses
    assert not bank.releases


def test_iphone_sound():
    bank = make_bank(parse_args(["--sound", "iphone"]), SR)
    assert set(bank.presses) == {"key", "wide", "space", "backspace"}
    assert not bank.releases


def test_synth_sound():
    bank = make_bank(parse_args(["--sound", "synth"]), SR)
    assert set(bank.presses) == {"key", "wide", "space"}
    assert set(bank.releases) == {"key", "wide", "space"}


def test_unknown_sound_is_rejected(capsys):
    with pytest.raises(SystemExit):
        parse_args(["--sound", "typewriter"])
    assert "invalid choice" in capsys.readouterr().err


def test_volume_must_be_positive(capsys):
    with pytest.raises(SystemExit):
        parse_args(["--volume", "0"])
    assert parse_args(["--volume", "0.5"]).volume == 0.5
