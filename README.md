# Creamy Keyboard Sound

Every key you press on your laptop sounds like a creamy custom mechanical
keyboard: a deep, soft, smooth *thock* instead of a flat plastic tap.

- Works everywhere: in your browser, chats, games and documents.
- Long keys (space, enter, backspace, shift, tab, caps lock) sound deeper, like
  real stabilised keys.
- Every key has its own slightly different pitch, and no two presses are
  exactly the same, so it never sounds robotic.
- A soft upstroke sound when you let go of a key.
- Holding a key down plays one sound, not a machine gun.
- Very low lag, with no delay between the press and the sound.
- **Ctrl+Alt+M** (on a Mac: **Control+Option+M**) mutes and unmutes it.

The sounds are synthesised by the program itself, so there is nothing to
download. You can also [use your own recordings](#use-your-own-sounds).

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

## Make it yours

Add any of these after the start command, for example
`start-windows.bat --volume 0.6 --pitch 0.9`. To make an option stick when you
double-click, open the start file in Notepad (or any text editor) and add it
after `creamy_keys` on the line that runs `creamy_keys`.

| Option | What it does |
| --- | --- |
| `--volume 0.5` | Quieter (or louder with e.g. `1.5`). |
| `--pitch 0.85` | Deeper and thockier. Above `1` sounds lighter and poppier. |
| `--no-release` | No sound when you let go of a key. |
| `--demo` | Plays a short typing demo, to test your speakers. |
| `--list-devices` | Shows your sound outputs. |
| `--device 3` | Plays on output 3 from that list (a name works too). |
| `--pack FOLDER` | Uses your own sounds (see below). |
| `--export FOLDER` | Saves the built-in sounds as WAV files. |

## Use your own sounds

If you have recordings of a keyboard you love, put them as WAV files in a
folder and start with `--pack path/to/folder`. Name the files after the key:

| File | Used for |
| --- | --- |
| `key.wav` (required) | Every key that has no file of its own |
| `space.wav` | Space bar |
| `wide.wav` | All long keys: enter, backspace, shift, tab, caps lock |
| `enter.wav`, `backspace.wav`, `shift.wav`, `tab.wav` … | That one key |
| `release.wav`, `space-release.wav` … | Sound when the key is let go |

Several versions of the same sound make it more natural. Number them, like
`key1.wav`, `key2.wav`, `key3.wav`, and one is picked at random for each press.
To see a complete example, run with `--export my-pack` and look at the files.

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

- `creamy_keys/synth.py`: how the creamy sound is built (tap, thock, pop).
- `creamy_keys/keys.py`: which keys get which sound, and auto-repeat detection.
- `creamy_keys/mixer.py`: low-latency playback of overlapping sounds.
- `creamy_keys/app.py`: connects the keyboard to the sounds.
