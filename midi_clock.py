"""
MIDI Clock Master Generator Module

This module handles the generation and transmission of MIDI realtime clock messages
using python-rtmidi on Linux/ALSA. It maintains precise timing using a high-resolution
timer and sends:
  - 0xFA: Start message (once at playback start)
  - 0xF8: Clock message (24 clocks per quarter note - PPQN)
  - 0xFC: Stop message (once at playback stop)

Timing assumptions:
  - Uses time.perf_counter() for high-resolution monotonic timing
  - Clock interval = 60 / (BPM * 24) seconds
  - Target resolution: microsecond-level precision for MIDI slave synchronization
  - Suitable for ALSA MIDI on Linux; target for Raspberry Pi migration
"""

import rtmidi
import threading
import time
from typing import Optional, Callable


class MIDIClockMaster:
    """
    Generates MIDI realtime messages (Start, Clock, Stop) with precise timing.
    
    MIDI realtime messages are single-byte commands:
      0xFA: Start
      0xF8: Clock (sent at PPQN rate, typically 24 per quarter note)
      0xFC: Stop
    
    This class manages:
    - Virtual MIDI output port creation
    - Precise clock generation at specified BPM
    - Thread-safe start/stop control
    - Runtime BPM changes
    """
    
    # MIDI realtime message bytes
    MIDI_START = 0xFA
    MIDI_CLOCK = 0xF8
    MIDI_STOP = 0xFC
    MIDI_PPQN = 24  # Standard: 24 MIDI clocks per quarter note
    
    def __init__(self, port_name: str = "ClockMaster", bpm: float = 120.0):
        """
        Initialize the MIDI clock master.
        
        Args:
            port_name: Name of the virtual MIDI output port
            bpm: Initial tempo in beats per minute (default 120)
        """
        self.port_name = port_name
        self.bpm = bpm
        self._running = False
        self._lock = threading.RLock()
        self._clock_thread: Optional[threading.Thread] = None
        
        # Beat callback for direct synchronization (called on beat boundary)
        self.on_beat: Optional[Callable[[], None]] = None
        
        # Initialize MIDI output
        self.midiout = rtmidi.MidiOut()
        try:
            # Create virtual output port (ALSA backend on Linux)
            self.midiout.open_virtual_port(port_name)
        except Exception as e:
            # Fallback: open default MIDI output if virtual fails
            print(f"Warning: Could not create virtual port '{port_name}': {e}")
            print("Attempting to use default MIDI output...")
            ports = self.midiout.get_ports()
            if ports:
                self.midiout.open_port(0)
            else:
                self.midiout.open_virtual_port(port_name)
        
    def _compute_clock_interval(self) -> float:
        """
        Compute the interval between MIDI clock messages.
        
        Formula: Clock interval (seconds) = 60 / (BPM * PPQN)
        Example: At 120 BPM with 24 PPQN: 60 / (120 * 24) = 0.02083 seconds
        
        Returns:
            Interval in seconds between consecutive MIDI clock messages
        """
        return 60.0 / (self.bpm * self.MIDI_PPQN)
    
    def start(self) -> None:
        """
        Start MIDI clock generation in a background thread.
        Sends MIDI Start (0xFA) immediately and begins clock generation.
        """
        with self._lock:
            if self._running:
                return  # Already running
            
            self._running = True
            # Send Start message
            self.midiout.send_message([self.MIDI_START])
            
            # Start background clock thread
            self._clock_thread = threading.Thread(
                target=self._run_clock_loop,
                daemon=True
            )
            self._clock_thread.start()
    
    def stop(self) -> None:
        """
        Stop MIDI clock generation and send MIDI Stop (0xFC).
        Waits for the clock thread to exit cleanly.
        """
        with self._lock:
            if not self._running:
                return  # Already stopped
            
            self._running = False
        
        # Wait for clock thread to finish
        if self._clock_thread and self._clock_thread.is_alive():
            self._clock_thread.join(timeout=2.0)
        
        # Send Stop message
        self.midiout.send_message([self.MIDI_STOP])
    
    def set_bpm(self, bpm: float) -> None:
        """
        Change the tempo at runtime.
        
        Args:
            bpm: New tempo in beats per minute
        """
        with self._lock:
            self.bpm = max(1.0, bpm)  # Ensure positive BPM
    
    def _run_clock_loop(self) -> None:
        """
        Main clock generation loop running in background thread.
        
        Uses perf_counter for timing but is lenient on jitter between individual
        clocks. As long as phase doesn't slip over 3-4 beats, minor timing
        variations are acceptable.
        
        Sets _beat_occurred flag when a beat boundary is reached (every 24 clocks)
        so that metronome can play audio in sync with MIDI clock.
        """
        clock_count = 0
        next_clock_time = time.perf_counter()
        
        while self._running:
            current_time = time.perf_counter()
            time_until_next = next_clock_time - current_time
            
            if time_until_next > 0:
                # Sleep for a portion of remaining time (with larger margin for stability)
                # Using 5ms margin reduces CPU busy-waiting while accepting minor jitter
                sleep_time = max(0.0001, time_until_next - 0.005)  # 5ms margin for stability
                time.sleep(sleep_time)
            else:
                # Time to send clock
                with self._lock:
                    # Recompute interval in case BPM changed
                    interval = self._compute_clock_interval()
                
                # Send MIDI clock message
                self.midiout.send_message([self.MIDI_CLOCK])
                
                # Check if this is a beat boundary (every 24 clocks)
                if clock_count % self.MIDI_PPQN == 0:
                    # Call beat callback directly for immediate audio trigger
                    # This runs in the MIDI thread for minimal latency
                    if self.on_beat:
                        self.on_beat()
                
                self.clock_count = clock_count
                clock_count += 1
                next_clock_time += interval
    
    def get_bpm(self) -> float:
        """Return current BPM."""
        with self._lock:
            return self.bpm
    
    def is_running(self) -> bool:
        """Return True if clock is currently running."""
        with self._lock:
            return self._running
    
    def __del__(self):
        """Clean up MIDI resources."""
        try:
            if self._running:
                self.stop()
            if hasattr(self, 'midiout'):
                del self.midiout
        except:
            pass
