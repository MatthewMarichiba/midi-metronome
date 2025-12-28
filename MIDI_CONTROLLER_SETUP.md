# TODO: THROW THIS AWAY.

# MIDI Controller UI Setup Guide

## Quick Start

1. **Connect your MIDI controller** to your computer via USB

2. **List available MIDI devices** to verify connection:
   ```bash
   python3 -c "import rtmidi; midiin = rtmidi.MidiIn(); print('\n'.join(midiin.get_ports()))"
   ```

3. **Launch the metronome** with MIDI UI:
   ```bash
   python3 main.py --ui midi --midi-controller "Arturia"
   ```
   
   Replace `"Arturia"` with the name (or part of the name) of your controller from step 2.

## Customizing CC Mappings

### Method 1: Edit the default mapping

Edit `ui_midi.py` and modify the `DEFAULT_CC_MAP` dictionary:

```python
DEFAULT_CC_MAP = {
    'start_stop': 20,      # Change to your preferred CC
    'mute': 21,
    # ... etc
}
```

### Method 2: Use a custom configuration

1. Create a new Python file (e.g., `my_config.py`):

```python
from ui_midi import MIDIUIController

my_cc_map = {
    'start_stop': 64,
    'mute': 65,
    'tap_tempo': 66,
    'bpm_coarse': 1,
    # Add only the controls you need
}

controller = MIDIUIController(
    controller_name="MyController",
    cc_map=my_cc_map
)
```

2. Modify `main.py` to use your custom configuration

### Method 3: Command-line with environment variable

For more advanced usage, you could create a launcher script that sets up custom mappings.

## Finding CC Numbers

If you're not sure which CC numbers your controller sends:

1. **Use a MIDI monitor:**
   ```bash
   aseqdump -p "YourController"
   ```
   
   Then press buttons/turn knobs and observe the CC numbers.

2. **Or use Python:**
   ```python
   import rtmidi
   import time
   
   midiin = rtmidi.MidiIn()
   ports = midiin.get_ports()
   
   # Find and open your controller
   for i, port in enumerate(ports):
       if "YourController" in port:
           midiin.open_port(i)
           break
   
   print("Press buttons/turn knobs. Press Ctrl+C to exit.")
   try:
       while True:
           msg = midiin.get_message()
           if msg:
               print(f"MIDI: {msg[0]}")
           time.sleep(0.01)
   except KeyboardInterrupt:
       pass
   ```

## Supported Commands

The MIDI controller UI supports these commands (all optional in your mapping):

| Command | Type | Description |
|---------|------|-------------|
| `start_stop` | Button | Toggle metronome on/off |
| `mute` | Button | Toggle audio mute |
| `tap_tempo` | Button | Tap to set BPM (averages last 5 taps) |
| `bpm_coarse` | Continuous | CC value 0-127 → BPM 20-300 |
| `bpm_fine_up` | Button | Increase BPM by 1 |
| `bpm_fine_down` | Button | Decrease BPM by 1 |
| `bpm_jump_up` | Button | Increase BPM by 5 |
| `bpm_jump_down` | Button | Decrease BPM by 5 |
| `divisions_up` | Button | Increase beat divisions |
| `divisions_down` | Button | Decrease beat divisions |
| `quit` | Button | Quit (requires double-press) |

**Button type**: Responds when CC value ≥ 64, ignores release (value < 64)  
**Continuous type**: Uses the full CC value range (0-127)

## Tips

- **Start minimal**: Map only the controls you need (start/stop, mute, BPM)
- **Button vs Continuous**: Buttons/pads work well for toggles and discrete changes. Faders/knobs work well for the `bpm_coarse` control.
- **Tap tempo**: Requires at least 2 taps to calculate BPM. Resets after 3 seconds of inactivity.
- **Quit safety**: The quit button requires a double-press within 2 seconds to prevent accidental exits.

## Troubleshooting

**"Could not find MIDI controller"**
- Run the device listing command from step 2 above
- Make sure the controller is connected and powered on
- Try a shorter/different substring of the device name

**CC messages not responding**
- Use `aseqdump` to verify your controller sends CC messages
- Check that the CC numbers in your mapping match what your controller sends
- Some controllers need to be in a specific mode to send CC messages

**Permission denied errors**
- Add your user to the `audio` group: `sudo usermod -a -G audio $USER`
- Log out and back in for the change to take effect
