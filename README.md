# MIDI Clock Master and Metronome

A Python-based MIDI clock master and metronome designed to control external devices (Boomerang III, Helix Floor) on Linux with ALSA MIDI. This system provides precise timing synchronization and optional audio click feedback.

## Architecture

The system consists of three modules:

1. **`midi_clock.py`** - Core MIDI realtime message generation
   - Generates MIDI Start (0xFA), Clock (0xF8), and Stop (0xFC) messages
   - Maintains 24 PPQN (pulses per quarter note) standard timing
   - Thread-safe with runtime BPM control
   - Creates virtual ALSA MIDI output port

2. **`metronome.py`** - Audio click at regular beat intervals
   - Generates click sounds at configurable BPM
   - Uses subprocess (aplay/ffplay) for audio - stable on all systems
   - Runs independent timing loop (no MIDI clock dependency)
   - Optional; can be disabled for MIDI-only operation

3. **`clock_master.py`** - Integration layer
   - Unified API for MIDI and audio control
   - Synchronizes metronome click to MIDI clock

4. **`main.py`** - Interactive command-line interface
   - Start/stop playback
   - Runtime tempo (BPM) changes
   - Enable/disable click sound

## Installation

### Linux (Ubuntu/Debian)

1. Install ALSA MIDI development headers and audio tools:
```bash
sudo apt-get install libasound2-dev python3-dev alsa-utils
```

2. Clone or navigate to the project directory:
```bash
cd midi-metronome
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Raspberry Pi

The code is designed to run on Raspberry Pi with minimal modifications:
1. Install Raspberry Pi OS with audio support
2. Install ALSA MIDI headers: `sudo apt-get install libasound2-dev`
3. Install Python packages as above
4. Optionally configure ALSA for optimal performance

## Usage

### Basic Usage

```bash
python3 main.py --bpm 120
```

### With Custom Click Sound

```bash
python3 main.py --bpm 140 --click /path/to/click.wav
```

### Without Click Sound (MIDI Only)

```bash
python3 main.py --bpm 100 --no-click
```

### Command-Line Options

```
--bpm BPM           Initial tempo in beats per minute (default: 120)
--click WAVFILE     Path to WAV file for metronome click
--no-click          Disable metronome click sound
--port NAME         Name of MIDI virtual output port (default: ClockMaster)
```

## Interactive Commands

Once the program starts, you can control it with these commands:

| Command | Description |
|---------|-------------|
| `start` | Start MIDI clock and metronome |
| `stop` | Stop clock and metronome |
| `bpm <value>` | Change tempo (e.g., `bpm 140`) |
| `click on/off` | Enable/disable click sound |
| `status` | Show current settings |
| `quit` | Exit program |

## Timing Specifications

### Clock Generation
- **PPQN (Pulses Per Quarter Note):** 24 (standard MIDI)
- **Clock Interval:** 60 / (BPM × 24) seconds
  - At 120 BPM: 20.83 ms between clocks
  - At 100 BPM: 25 ms between clocks
  - At 140 BPM: 17.86 ms between clocks

### Precision
- Uses `time.perf_counter()` for high-resolution monotonic timing
- Sleep resolution: microsecond-level with 1ms safety margin
- Suitable for slave device quantization (Boomerang III, Helix Floor)

### MIDI Messages
- **0xFA** - Start message (sent once at playback start)
- **0xF8** - Clock message (sent at PPQN rate)
- **0xFC** - Stop message (sent at playback stop)

## Audio Click

The metronome plays a click sound at regular beat intervals. Features:

- Independent timing loop (runs in separate thread)
- Uses system audio tools (aplay/ffplay) - stable on all systems
- Subprocess-based - avoids threading issues with audio libraries
- Optional: can be disabled with `--no-click` or `click off`
- Thread-safe operation

## System Architecture Notes

### Why Not JACK?
This system uses ALSA MIDI directly because:
- JACK adds unnecessary complexity for clock master use case
- Direct ALSA MIDI offers lower latency
- JACK is optional; slave devices can connect via ALSA

### Thread Safety
- Background clock thread maintains real-time generation
- Mutex-protected BPM changes
- Safe for runtime modifications without stopping/restarting

### Raspberry Pi Compatibility
All modules use:
- Pure Python (no C bindings except `python-rtmidi`)
- Standard Linux/ALSA APIs
- Minimal dependencies
- No GUI framework (command-line only)

Code can be moved to Raspberry Pi with no changes.

## Integration with Slave Devices

This system is designed to control:
- **Boomerang III Loop Pedal** - Listens to MIDI clock for loop quantization
- **Helix Floor** - Uses MIDI clock for synchronized effects

To use with these devices:
1. Connect via USB or MIDI interface
2. Configure each device to listen to "ClockMaster" or your configured port name
3. Set both devices as "MIDI slave" or similar
4. Run `python3 main.py` with desired BPM

## Troubleshooting

### "Could not create virtual port" error
This may occur if ALSA MIDI sequencer is not running. Try:
```bash
# Start ALSA sequencer daemon
sudo systemctl start alsa-utils
```

Or on Raspberry Pi:
```bash
# Ensure ALSA is installed
sudo apt-get install alsa-utils
```

### No MIDI output visible in slave devices
- Verify slave device is configured to listen to "ClockMaster" port
- Check MIDI connections: `aconnect -o` (shows output ports)
- Ensure `python3 main.py` is running before connecting slave device

### Audio click not playing
- Verify WAV file exists and is readable
- Check ALSA audio levels: `alsamixer`
- Ensure audio output device is selected and unmuted
- Try generating sample click: `python3 main.py` (without `--click` option)

## Development Notes

### Code Organization
- **Timing** - `midi_clock.py` handles all MIDI clock generation
- **Audio** - `metronome.py` isolated from MIDI logic
- **Integration** - `clock_master.py` combines the two
- **CLI** - `main.py` provides user interface

### Adding Features
Examples of potential extensions:
- Swing/shuffle timing
- Different click patterns (e.g., accent on beat 1)
- MIDI learn for slave device configuration
- Tap tempo input
- Web-based remote control

### Testing
To test core clock generation:
```python
from midi_clock import MIDIClockMaster
import time

master = MIDIClockMaster(bpm=120)
master.start()
time.sleep(5)
master.stop()
```

## License

[Add your license here]

## References

- [MIDI Specification](https://www.midi.org/)
- [python-rtmidi](https://github.com/SpotlightKid/python-rtmidi)
- [simpleaudio](https://github.com/spatialaudio/python-simpleaudio)
- [ALSA Project](https://www.alsa-project.org/)
