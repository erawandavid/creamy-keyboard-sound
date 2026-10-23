from creamy_keys.keys import REPEAT_WINDOW, KeyTracker, classify, normalise


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def test_normalise_merges_left_and_right_keys():
    assert normalise("shift_r") == "shift"
    assert normalise("ctrl_l") == "ctrl"
    assert normalise("alt_gr") == "alt"
    assert normalise("caps_lock") == "caps_lock"


def test_normalise_maps_space_character():
    assert normalise(" ") == "space"


def test_ctrl_letters_reported_as_control_characters_use_the_key_sound():
    # Windows reports Ctrl+M as "\r" and Ctrl+H as "\b".
    assert classify("\r") == ("key",)
    assert classify("\b") == ("key",)


def test_classify_letters_and_unknown_keys_use_the_key_sound():
    assert classify("a") == ("key",)
    assert classify("A") == ("key",)
    assert classify("") == ("key",)
    assert classify("esc") == ("esc", "key")


def test_classify_long_keys():
    assert classify("space") == ("space", "key")
    assert classify(" ") == ("space", "key")
    assert classify("enter") == ("enter", "wide", "key")
    assert classify("shift_r") == ("shift", "wide", "key")
    assert classify("backspace") == ("backspace", "wide", "key")


def test_tracker_ignores_auto_repeat():
    clock = FakeClock()
    tracker = KeyTracker(clock)
    assert tracker.press("a")
    for _ in range(20):
        clock.now += 0.03
        assert not tracker.press("a")
    assert tracker.release("a")
    assert tracker.press("a")


def test_tracker_recovers_from_a_missed_release():
    clock = FakeClock()
    tracker = KeyTracker(clock)
    assert tracker.press("a")
    clock.now += REPEAT_WINDOW + 0.1
    assert tracker.press("a")


def test_tracker_release_of_unknown_key():
    tracker = KeyTracker(FakeClock())
    assert not tracker.release("a")
    tracker.press("a")
    assert not tracker.release("b")
    assert tracker.release("a")
    assert not tracker.release("a")
