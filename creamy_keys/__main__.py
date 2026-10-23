"""Command line: ``python -m creamy_keys``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .app import MUTE_SHORTCUT, CreamyKeyboard, demo, listen
from .bank import BUILTIN_PACK, SoundBank, load_pack, synthesize
from .mixer import AudioOutput, Mixer, list_devices, parse_device
from .synth import PHONE_PROFILES

SOUNDS = ("cream", "iphone", "synth")


def positive(text: str) -> float:
    value = float(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be more than 0")
    return value


def parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="creamy-keys",
        description="Make every key on your computer sound like a creamy mechanical keyboard.",
    )
    parser.add_argument("--volume", type=positive, default=1.0,
                        help="loudness, e.g. 0.5 for half as loud (default: 1.0)")
    parser.add_argument("--pitch", type=positive, default=1.0,
                        help="below 1 is deeper and thockier, above 1 is lighter (default: 1.0)")
    parser.add_argument("--no-release", action="store_true",
                        help="stay silent when a key is let go")
    parser.add_argument("--sound", choices=SOUNDS, default="cream",
                        help="cream: recordings of NovelKeys Cream switches (default); "
                             "iphone: short, crisp phone-style taps; "
                             "synth: a computer-generated thock")
    parser.add_argument("--pack", type=Path, metavar="FOLDER",
                        help="use your own WAV sounds from FOLDER instead (see README)")
    parser.add_argument("--device", help="audio output to use, by number or name")
    parser.add_argument("--list-devices", action="store_true",
                        help="list the audio outputs and exit")
    parser.add_argument("--demo", action="store_true",
                        help="play a short typing demo and exit, to test your speakers")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def make_bank(args: argparse.Namespace, samplerate: int) -> SoundBank:
    if args.pack:
        return load_pack(args.pack, samplerate)
    if args.sound == "iphone":
        return synthesize(samplerate, PHONE_PROFILES, with_releases=False)
    if args.sound == "synth":
        return synthesize(samplerate)
    return load_pack(BUILTIN_PACK, samplerate)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    try:
        if args.list_devices:
            print(list_devices())
            return 0
        mixer = Mixer(volume=args.volume)
        output = AudioOutput(mixer, parse_device(args.device))
    except (OSError, RuntimeError, ValueError) as e:
        print(f"Could not start the sound: {e}", file=sys.stderr)
        if "PortAudio" in str(e):
            print("On Linux, install it with: sudo apt install libportaudio2", file=sys.stderr)
        return 1

    try:
        bank = make_bank(args, output.samplerate)
    except (OSError, ValueError) as e:
        print(f"Could not load the sound pack: {e}", file=sys.stderr)
        return 1

    def on_mute(muted: bool) -> None:
        print("Muted." if muted else "Unmuted, creamy again.", flush=True)

    keyboard = CreamyKeyboard(
        bank, mixer, pitch=args.pitch, release_sounds=not args.no_release, on_mute=on_mute
    )

    output.start()
    try:
        if args.demo:
            demo(keyboard)
        else:
            print(
                f"Creamy keys are ON ({args.pack or args.sound}) - type anywhere.\n"
                f"  {MUTE_SHORTCUT:<17} mute / unmute\n"
                "  Ctrl+C            quit (or close this window)\n"
                f"Playing through: {output.device_name}",
                flush=True,
            )
            listen(keyboard)
    except KeyboardInterrupt:
        pass
    except ImportError as e:  # pynput cannot reach the keyboard on this system
        print(f"Could not listen to the keyboard: {e}", file=sys.stderr)
        return 1
    finally:
        output.close()
    print("Bye!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
