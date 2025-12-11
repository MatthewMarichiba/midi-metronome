# Raspberry Pi Setup Guide

This guide provides step-by-step instructions for setting up the MIDI Clock Master on Raspberry Pi.

## Prerequisites

- Raspberry Pi (3B+ or later recommended)
- Raspberry Pi OS (32-bit or 64-bit)
- Ethernet or Wi-Fi connection
- Optional: USB MIDI interface or GPIO-based MIDI output

## Installation Steps

### 1. Update System Packages

```bash
sudo apt-get update
sudo apt-get upgrade
```

### 2. Install Audio and MIDI Dependencies

```bash
# Core audio/MIDI libraries
sudo apt-get install libasound2-dev python3-dev

# Optional: for advanced ALSA configuration
sudo apt-get install alsa-utils

# Optional: MIDI tools for testing
sudo apt-get install alsa-midi-utils
```

### 3. Install Python and pip

```bash
# Usually pre-installed on Raspberry Pi OS
sudo apt-get install python3 python3-pip

# Verify installation
python3 --version
```

### 4. Clone or Copy the Project

```bash
cd ~
git clone <repository-url> midi-metronome
cd midi-metronome
```

Or copy files manually to `~/midi-metronome`

### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note:** This may take a few minutes on Raspberry Pi, especially `simpleaudio` compilation.

### 6. Set Up Audio Output

#### For HDMI Audio
```bash
# List available audio devices
aplay -l

# Set HDMI as default
sudo raspi-config
# Select: Advanced Options > Audio > HDMI
# Reboot
```

#### For 3.5mm Jack
```bash
sudo raspi-config
# Select: Advanced Options > Audio > Jack
# Reboot
```

#### For USB Audio Device
```bash
# Connect USB audio interface
aplay -l  # Should show USB device

# Edit ~/.asoundrc if needed for default output
```

### 7. Create Systemd Service (Optional)

To run the clock master at boot or as a service:

**1. Create service file:**
```bash
sudo nano /etc/systemd/system/midi-clock.service
```

**2. Add this content:**
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
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**3. Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable midi-clock.service
sudo systemctl start midi-clock.service

# Check status
sudo systemctl status midi-clock.service
```

### 8. Test Installation

```bash
# Run basic test
python3 test_clock.py

# Run interactive clock
python3 main.py --bpm 120 --no-click

# Test with audio (if audio device is configured)
python3 main.py --bpm 120
```

## MIDI Connection Setup

### USB MIDI Interface

1. Connect USB MIDI interface to Raspberry Pi
2. Check connection:
```bash
aconnect -o
```
3. You should see output ports including "ClockMaster"

### GPIO MIDI Output (Advanced)

For direct MIDI output via GPIO (no USB required):

1. Install `pisound-btn` or similar GPIO MIDI driver
2. Configure ALSA MIDI to route through GPIO
3. Connect hardware (MIDI connector to GPIO pins)

See Raspberry Pi MIDI GPIO project documentation for details.

## Performance Optimization

### Real-Time Priority

For improved timing consistency:

```bash
# Edit /etc/security/limits.conf
sudo nano /etc/security/limits.conf

# Add at end:
pi              -       rtprio          90
pi              -       memlock         unlimited
```

### CPU Frequency Scaling

Disable frequency scaling for consistent timing:

```bash
# Edit /boot/firmware/config.txt (or /boot/config.txt on older Pi)
sudo nano /boot/firmware/config.txt

# Add or modify:
# Force maximum CPU frequency
force_turbo=1

# Reboot to apply
sudo reboot
```

### Disable Unused Services

Reduce CPU load:

```bash
# Disable unneeded services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
sudo systemctl disable cups

# Disable automatic updates if not needed
sudo systemctl disable apt-daily.timer
sudo systemctl disable apt-daily-upgrade.timer
```

## Troubleshooting

### ALSA Sequencer Not Running

If you see "Cannot open sequencer" errors:

```bash
# Start ALSA sequencer daemon
sudo systemctl start alsa-seq

# Enable for boot
sudo systemctl enable alsa-seq
```

### Audio Issues

```bash
# Check audio device
aplay -l
arecord -l

# Test audio playback
speaker-test -t sine -f 440 -l 2
```

### MIDI Port Not Appearing

```bash
# List MIDI ports
aconnect -l -o

# Check syslog for errors
sudo journalctl -n 50 | grep -i midi
```

### Python Package Installation Fails

If `simpleaudio` fails to compile:

```bash
# Install additional build dependencies
sudo apt-get install build-essential
sudo apt-get install pulseaudio-dev  # or alsa-lib-dev

# Retry installation
pip install --force-reinstall simpleaudio
```

## Running at Startup

### Option 1: Systemd Service (Recommended)
Follow "Create Systemd Service" section above.

### Option 2: Crontab

```bash
crontab -e

# Add line (runs at boot):
@reboot sleep 10 && /usr/bin/python3 /home/pi/midi-metronome/main.py --bpm 120
```

### Option 3: rc.local

```bash
sudo nano /etc/rc.local

# Add before exit 0:
/usr/bin/python3 /home/pi/midi-metronome/main.py --bpm 120 &
```

## Remote Control

### SSH Access

```bash
# SSH into Raspberry Pi
ssh pi@<ip-address>

# Run clock master
cd midi-metronome
python3 main.py
```

### Web Interface (Future Enhancement)

For web-based control, add Flask API layer to `main.py`:

```python
from flask import Flask, jsonify, request

app = Flask(__name__)
master = ClockMaster()

@app.route('/start', methods=['POST'])
def start_clock():
    master.start()
    return jsonify({'status': 'running'})

@app.route('/bpm/<float:bpm>', methods=['POST'])
def set_tempo(bpm):
    master.set_bpm(bpm)
    return jsonify({'bpm': master.get_bpm()})
```

## Power Management

### USB Power Supply
Use at least 2.5A (5V) power supply for stable operation.

### Reduce Power Consumption
- Disable HDMI: `tvservice -o`
- Use headless (no monitor)
- Disable unneeded interfaces: Wi-Fi, Bluetooth

## Benchmarks

Typical Raspberry Pi 4 performance:
- Clock timing accuracy: ±5ms (within acceptable range for looper quantization)
- MIDI message latency: ~1-2ms
- Audio click latency: ~20-50ms (depends on audio driver)

## References

- [Raspberry Pi Official Documentation](https://www.raspberrypi.com/documentation/)
- [ALSA Project](https://www.alsa-project.org/)
- [python-rtmidi Documentation](https://github.com/SpotlightKid/python-rtmidi)
- [Raspberry Pi MIDI Setup Guide](https://pimusicbox.com/)
