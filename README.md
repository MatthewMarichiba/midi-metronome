# MIDI Clock Master and Metronome

A Python-based MIDI clock master for controlling external devices (Boomerang III, Helix Floor) on Linux and Raspberry Pi. Provides precise timing synchronization with optional audio click feedback.

## Quick Start

### 1. Install System Dependencies

```bash
sudo apt-get install libasound2-dev python3-dev alsa-utils
```

### 2. Set Up Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Clock

```bash
python3 main.py --bpm 120 [--no-start]
```

Once running, use these commands:
- `start` - Start MIDI clock and audio click
- `stop` - Stop the clock
- `bpm 140` - Change tempo
- `status` - Show current settings
- `quit` - Exit

### 4. Connect the MIDI Metronome port output to the input of the MIDI device you want to receive clock input.

```
aseqdump -l  # List the available MIDI ports
aconnect 128:0 16:0  # Use the port numbers revealed by aseqdump.
```

## Usage Options

* `--bpm X` - Initialize with given beats-per-minute value
* `--no-click` - MIDI only (no audio)
* `--no-start` - Don't auto-start the clock. Wait for command-line prompt.

## Architecture

- **`midi_clock.py`** - MIDI realtime message generation with beat callbacks
- **`audio.py`** - Synthesized click tone generation and playback
- **`main.py`** - Interactive command-line interface
- **`ui_controller.py`** - Abstract base class for UI controllers
- **`ui_keyboard.py`** - Single-keypress keyboard interface
- **`ui_midi.py`** - MIDI controller interface with configurable CC mapping
- **`ui_legacy.py`** - Legacy line-based interface
- **`diag_clock.py`** - Diagnostic clock for testing

## Raspberry Pi Notes

Works on Pi 3B+ or later without modification. For optimal timing:

```bash
# Edit /boot/firmware/config.txt (or /boot/config.txt on older Pi)
sudo nano /boot/firmware/config.txt

# Add:
force_turbo=1

# Reboot
sudo reboot
```

To run at boot, create `/etc/systemd/system/midi-clock.service`:

```ini
[Unit]
Description=MIDI Clock Master
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/midi-metronome
ExecStart=/usr/bin/python3 /home/pi/midi-metronome/main.py --bpm 120
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable midi-clock.service
sudo systemctl start midi-clock.service
```

## License

MIT License - See LICENSE file for details.
