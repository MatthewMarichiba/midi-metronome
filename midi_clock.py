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
    
    def __init__(self, port_name: str = "MIDI Metronome", bpm: float = 60.0, target: str = "HELIX", beat_callback=None, divisions: int = 1, audio_muted: bool = False):
        """Initialize MIDI Clock Master.
        
        Args:
            port_name: Name of the virtual MIDI port to create
            bpm: Beats per minute (default: 60.0)
            target: Target MIDI device to auto-connect to (default: HELIX)
            beat_callback: Callable invoked on each beat edge (optional)
            divisions: Number of division ticks per beat (default: 1)
            audio_muted: Start with audio muted (default: False)
        """
        # Tempo and timing
        self.bpm = bpm  # Beats per minute
        self.divisions = divisions  # Number of ticks per beat. Not used in this class, but stored here because it is part of clock state.
        self.clock_count = 0  # Total MIDI clock ticks since start
        
        # State and threading
        self._running = False  # Clock loop active flag
        self._lock = threading.RLock()  # Thread-safe state access
        self._clock_thread: Optional[threading.Thread] = None  # Clock loop thread
        
        # Audio callback
        self.on_beat: Callable[[], None] = beat_callback or (lambda: None)  # Called on beat edges
        self.audio_muted = audio_muted  # Mute audio clicks
        
        # MIDI output
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
    
    def set_bpm(self, bpm: float) -> None:
        """Change BPM and restart the clock if running."""
        was_running = self._running
        if was_running:
            self.stop()
        self.bpm = bpm
        if was_running:
            self.start()

    def mute_audio(self) -> None:
        """Disable audio clicks."""
        self.audio_muted = True
    
    def unmute_audio(self) -> None:
        """Enable audio clicks."""
        self.audio_muted = False
    
    def _run_clock_loop(self) -> None:
        """Main clock loop with absolute time synchronization using interval-timer."""
        period = 60.0 / (self.bpm * self.MIDI_PPQN)
        timer = IntervalTimer(period=period)

        # Send MIDI Start message        
        self.midiout.send_message([self.MIDI_START])

        for _ in timer:
            if not self._running:
                break
            
            # Send MIDI clock
            self.midiout.send_message([self.MIDI_CLOCK])
            
            # Play beat pattern at beat edges
            if not self.audio_muted and self.clock_count % self.MIDI_PPQN == 0:
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
