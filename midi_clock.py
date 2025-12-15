"""MIDI Clock Master - generates precise MIDI realtime messages."""

import rtmidi
import threading
from interval_timer import IntervalTimer
from typing import Optional, Callable


class MIDIClockMaster:
    """Simple MIDI clock generator with beat callback."""
    
    MIDI_START = 0xFA
    MIDI_CLOCK = 0xF8
    MIDI_STOP = 0xFC
    MIDI_PPQN = 24
    
    def __init__(self, port_name: str = "MIDI Metronome", bpm: float = 120.0):
        self.bpm = bpm
        self._running = False
        self._lock = threading.RLock()
        self._clock_thread: Optional[threading.Thread] = None
        self.on_beat: Optional[Callable[[], None]] = None
        self.clock_count = 0
        
        self.midiout = rtmidi.MidiOut()
        try:
            self.midiout.open_virtual_port(port_name)
        except Exception as e:
            print(f"Warning: Could not create virtual port '{port_name}': {e}")
            ports = self.midiout.get_ports()
            if ports:
                self.midiout.open_port(0)
            else:
                self.midiout.open_virtual_port(port_name)
    
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
    
    def set_bpm(self, bpm: float) -> None:
        """Change BPM and restart the clock if running."""
        was_running = self._running
        if was_running:
            self.stop()
        self.bpm = bpm
        if was_running:
            self.start()
    
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
