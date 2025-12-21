"""MIDI Clock Master - generates precise MIDI realtime messages."""

import rtmidi
import threading
import subprocess
from interval_timer import IntervalTimer
from typing import Optional, Callable


class MIDIClockMaster:
    """Simple MIDI clock generator with beat callback."""
    
    MIDI_START = 0xFA
    MIDI_CLOCK = 0xF8
    MIDI_STOP = 0xFC
    MIDI_PPQN = 24
    
    def __init__(self, port_name: str = "MIDI Metronome", bpm: float = 120.0, target: str = "HELIX"):
        self.bpm = bpm
        self.divisions = 1
        self._running = False
        self._lock = threading.RLock()
        self._clock_thread: Optional[threading.Thread] = None
        self.on_beat: Optional[Callable[[], None]] = None
        self.click_tone = None  # Store for unmute
        self.clock_count = 0
        
        self.midiout = rtmidi.MidiOut()
        self.midiout.set_client_name(port_name)
        try:
            self.midiout.open_virtual_port(port_name)
        except Exception as e:
            print(f"Warning: Could not create virtual port '{port_name}': {e}")
            ports = self.midiout.get_ports()
            if ports:
                self.midiout.open_port(0)
            else:
                self.midiout.open_virtual_port(port_name)
        
        # Auto-connect to target
        self._connect_to_target(port_name, target)
    
    def _connect_to_target(self, source_port: str, target_port: str) -> None:
        """Connect MIDI ports using aconnect."""
        try:
            # Use aconnect to connect the ports
            cmd = ["aconnect", f'"{source_port}":0', f'"{target_port}":0']
            cmd_str = " ".join(cmd)
            print(f"Executing: {cmd_str}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✓ Connected '{source_port}' → '{target_port}'")
            else:
                print(f"Warning: aconnect failed: {result.stderr.strip()}")
        except FileNotFoundError:
            print("Warning: aconnect not found. Install alsa-utils to enable auto-connect.")
        except subprocess.TimeoutExpired:
            print("Warning: aconnect timed out")
        except Exception as e:
            print(f"Warning: Failed to connect ports: {e}")
    
    def start(self) -> None:
        """Start MIDI clock generation."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self.midiout.send_message([self.MIDI_START])
            self._clock_thread = threading.Thread(
                target=self._run_clock_loop, daemon=True
            )
            self._clock_thread.start()
    
    def stop(self) -> None:
        """Stop MIDI clock generation."""
        with self._lock:
            if not self._running:
                return
            self._running = False
        
        if self._clock_thread and self._clock_thread.is_alive():
            self._clock_thread.join(timeout=2.0)
        
        self.midiout.send_message([self.MIDI_STOP])
    
    def set_bpm(self, bpm: float, divisions: int = 1) -> None:
        """Change BPM and divisions, restart the clock if running."""
        was_running = self._running
        if was_running:
            self.stop()
        self.bpm = bpm
        self.divisions = divisions
        if was_running:
            self.start()

    def mute_audio(self) -> None:
        """Disable audio click callback."""
        self.on_beat = None
    
    def unmute_audio(self, click_tone) -> None:
        """Enable audio click callback with the given tone."""
        from audio import play_click
        self.click_tone = click_tone
        self.on_beat = lambda: play_click(click_tone)
    
    def _run_clock_loop(self) -> None:
        """Main clock loop with absolute time synchronization using interval-timer."""
        period = 60.0 / (self.bpm * self.MIDI_PPQN)
        timer = IntervalTimer(period=period)
        
        for _ in timer:
            if not self._running:
                break
            
            # Send MIDI clock
            self.midiout.send_message([self.MIDI_CLOCK])
            
            # Beat callback on boundaries
            if self.clock_count % self.MIDI_PPQN == 0:
                if self.on_beat:
                    self.on_beat()
            
            self.clock_count += 1
    
    def __del__(self):
        try:
            if self._running:
                self.stop()
            if hasattr(self, 'midiout'):
                del self.midiout
        except:
            pass
