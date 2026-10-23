# Creamy Keyboard Sound

Every key you press on your laptop sounds like a creamy custom mechanical
keyboard instead of a flat plastic tap.

- The sounds are real recordings of a keyboard with **NovelKeys Cream**
  switches, the switch that "creamy" sounds are named after.
- Every letter has its own recording, made from that key on the real board,
  and space, enter, backspace, shift, tab and caps lock have theirs too.
- Works everywhere: in your browser, chats, games and documents.
- Holding a key down plays one sound, not a machine gun.
- Very low lag, with no delay between the press and the sound.
- **Ctrl+Alt+M** (on a Mac: **Control+Option+M**) mutes and unmutes it.

You can also [use your own recordings](#use-your-own-sounds).

## Start it

You need **Python 3.8 or newer**. If you don't have it, install it from
[python.org/downloads](https://www.python.org/downloads/). On Windows, tick
**"Add python.exe to PATH"** in the installer.

Then download this project (green **Code** button → **Download ZIP**) and
unzip it.

### Windows

Double-click **`start-windows.bat`**.

The first time, it takes a minute to set itself up. After that it starts right
away. Leave the window open (you can minimise it) while you type. Close the
window to stop the sounds.

### macOS

1. Open **Terminal**, type `sh ` (with a space), drag `start-mac-linux.sh` into
   the window and press Enter.
2. macOS will ask for permission the first time. Open **System Settings →
   Privacy & Security** and allow **Terminal** under both **Accessibility** and
   **Input Monitoring**.
3. Quit Terminal and run it again.

### Linux

```sh
sudo apt install libportaudio2   # once (Fedora: sudo dnf install portaudio)
./start-mac-linux.sh
```

On an X11 desktop this hears every key. On **Wayland** it only hears keys typed
into some apps, so use the system-wide input reader instead:

```sh
sudo usermod -aG input $USER     # once, then log out and back in
PYNPUT_BACKEND=uinput ./start-mac-linux.sh
```

### From the command line

Instead of downloading the ZIP by hand, you can install the `creamy-keys`
command with pip. Git is not needed.

Windows (Command Prompt or PowerShell):

```bat
py -m pip install https://github.com/erawandavid/creamy-keyboard-sound/archive/refs/heads/claude/modest-hawking-hxb3je.zip
py -m creamy_keys
```

macOS and Linux (in its own environment, so it doesn't touch the system Python):

```sh
python3 -m venv ~/.creamy-keys
~/.creamy-keys/bin/pip install https://github.com/erawandavid/creamy-keyboard-sound/archive/refs/heads/claude/modest-hawking-hxb3je.zip
~/.creamy-keys/bin/creamy-keys
```

Options go after the command, for example `py -m creamy_keys --volume 0.6`.
Run the same install command again to update.

## Make it yours

Add any of these after the start command, for example
`start-windows.bat --volume 0.6 --pitch 0.9`. To make an option stick when you
double-click, open the start file in Notepad (or any text editor) and add it
after `creamy_keys` on the line that runs `creamy_keys`.

| Option | What it does |
| --- | --- |
| `--volume 0.5` | Quieter (or louder with e.g. `1.5`). |
| `--pitch 0.85` | Deeper and thockier. Above `1` sounds lighter and poppier. |
| `--no-release` | No sound when you let go of a key (for sound packs that have one). |
| `--demo` | Plays a short typing demo, to test your speakers. |
| `--list-devices` | Shows your sound outputs. |
| `--device 3` | Plays on output 3 from that list (a name works too). |
| `--pack FOLDER` | Uses your own sounds (see below). |
| `--synth` | Uses computer-generated sounds instead of the recordings. |

## Use your own sounds

If you have recordings of a keyboard you love, put them as WAV files in a
folder and start with `--pack path/to/folder`. Name the files after the key:

| File | Used for |
| --- | --- |
| `key.wav` | Every key that has no file of its own |
| `a.wav`, `b.wav`, `5.wav` … | That one letter, number or symbol |
| `space.wav` | Space bar |
| `wide.wav` | All long keys: enter, backspace, shift, tab, caps lock |
| `enter.wav`, `backspace.wav`, `shift.wav`, `tab.wav` … | That one key |
| `release.wav`, `space-release.wav` … | Sound when the key is let go |

You need either `key.wav` or a file for each letter. If there is no
`key.wav`, other keys borrow the letters' sounds. Several versions of the same
sound make it more natural. Number them, like `key1.wav`, `key2.wav`,
`key3.wav`, and one is picked at random for each press. Silence around each
sound is cut off and the loudness is evened out automatically. For a complete
example, look at the built-in sounds in
[`creamy_keys/sounds/nk-cream`](creamy_keys/sounds/nk-cream).

Only use recordings you made yourself or that you have permission to use.

## Start it automatically

- **Windows:** press Win+R, type `shell:startup`, and put a shortcut to
  `start-windows.bat` in the folder that opens.
- **macOS:** System Settings → General → Login Items → add a small Automator
  app or shell script that runs `start-mac-linux.sh`.
- **Linux:** add `start-mac-linux.sh` to your desktop's "Startup Applications".

## Privacy

To hear your key presses, the program has to listen to the keyboard. It never
stores, logs or sends what you type. Nothing leaves your computer. The code
in [`creamy_keys/app.py`](creamy_keys/app.py) only uses each key to choose a
sound.

## For developers

```sh
python -m pip install -e ".[test]"
python -m pytest
python -m creamy_keys --help
```

- `creamy_keys/bank.py`: loads sound packs and evens them out.
- `creamy_keys/synth.py`: the computer-generated sound (`--synth`).
- `creamy_keys/keys.py`: which keys get which sound, and auto-repeat detection.
- `creamy_keys/mixer.py`: low-latency playback of overlapping sounds.
- `creamy_keys/app.py`: connects the keyboard to the sounds.

## Credits

The built-in sounds are the "NK Cream (original by Ryan)" pack from
[Mechvibes](https://github.com/hainguyents13/mechvibes), used under the MIT
License, Copyright (c) 2021 Hai Nguyen. See
[`creamy_keys/sounds/nk-cream/LICENSE.txt`](creamy_keys/sounds/nk-cream/LICENSE.txt).
