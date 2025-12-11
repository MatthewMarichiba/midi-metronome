# Quick Start Guide

## 5-Minute Setup

### 1. Create Virtual Environment
```bash
python3 -m venv .venv
```

### 2. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Clock
```bash
python3 main.py --bpm 120
```

### 5. Interactive Commands
```
> start              # Start clock and click
> bpm 140            # Change tempo to 140
> stop               # Stop clock
> quit               # Exit
```

## Common Use Cases

### MIDI Only (No Audio)
```bash
python3 main.py --no-click --bpm 120
```

### With Custom Click Sound
```bash
python3 main.py --click /path/to/click.wav --bpm 140
```

### Connect Slave Device (Boomerang/Helix)

Before running the clock:
1. Connect device via USB or MIDI interface
2. Configure device to listen to "ClockMaster" port
3. Run: `python3 main.py --bpm 120`
4. Device will synchronize to MIDI clock

### Programmatic Usage

```python
from clock_master import ClockMaster

# Create master
master = ClockMaster(bpm=120, click_wav="click.wav")

# Start clock
master.start()

# Change tempo
master.set_bpm(140)

# Stop
master.stop()
```

## Testing

```bash
# Run all tests
python3 test_clock.py

# Run specific test
python3 test_clock.py timing
python3 test_clock.py integration
```

## Files Overview

| File | Purpose |
|------|---------|
| `midi_clock.py` | MIDI realtime message generation (Start, Clock, Stop) |
| `metronome.py` | Audio click synchronized to MIDI clock |
| `clock_master.py` | Integration layer combining MIDI and audio |
| `main.py` | Interactive command-line interface |
| `test_clock.py` | Unit tests and validation |
| `requirements.txt` | Python dependencies |
| `README.md` | Full documentation |
| `ARCHITECTURE.md` | Technical design and internals |
| `RASPBERRY_PI_SETUP.md` | Raspberry Pi installation guide |

## Timing Basics

- **BPM to Clock Interval:** `60 / (BPM × 24)` seconds
  - 120 BPM = 20.83 ms per clock
  - 100 BPM = 25 ms per clock
  - 140 BPM = 17.86 ms per clock

- **Click Playback:** Every 24 MIDI clocks (one quarter note/beat)

- **Precision:** ±5-10ms jitter on Linux, ±20ms on Raspberry Pi (acceptable for looper quantization)

## Troubleshooting

**"Cannot open sequencer" error**
```bash
sudo systemctl start alsa-seq
```

**MIDI port not visible**
```bash
aconnect -o
# Should show ClockMaster port
```

**No audio playback**
```bash
aplay -l
# Check audio device is listed
```

## Next Steps

1. Read `README.md` for complete documentation
2. Review `ARCHITECTURE.md` for system design
3. Run `python3 test_clock.py` to validate setup
4. Connect your Boomerang III or Helix Floor
5. Customize click sound or extend with additional features

## Virtual Environment

A Python virtual environment isolates your project dependencies from system Python.

**First time setup (create the venv):**
```bash
python3 -m venv .venv
```

**Every time you work on the project (activate the venv):**
```bash
source .venv/bin/activate
```

**When done (deactivate):**
```bash
deactivate
```

**Why use a virtual environment?**
- Isolates project dependencies from system Python
- Prevents conflicts with other projects
- Follows Python best practices
- Safe for development and deployment

Always activate the venv before running `python3 main.py` or `pip install`.

## Troubleshooting Installation

**"externally-managed-environment" error when installing packages?**
This means you need to use a virtual environment (see above). Run:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**simpleaudio build fails during install?**
You need ALSA development headers:
```bash
sudo apt-get install libasound2-dev python3-dev
```
Then retry: `pip install -r requirements.txt`

## Support

For issues or questions, refer to:
- `README.md` - Configuration and usage
- `ARCHITECTURE.md` - Technical details
- `test_clock.py` - Validation tests
- Code comments - Implementation details
