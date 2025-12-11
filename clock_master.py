"""
Clock Master Integration Module

Combines MIDIClockMaster and MetronomeClick into a unified interface
for generating synchronized MIDI clock and audio metronome clicks.

This is the primary API for controlling the MIDI metronome system.
"""

from midi_clock import MIDIClockMaster
from metronome import MetronomeClick
from typing import Optional
import threading


class ClockMaster:
    """
    Unified MIDI clock master with integrated metronome audio.
    
    Manages:
      - MIDI realtime message generation (Start, Clock, Stop)
      - Synchronized audio click playback
      - Runtime tempo control
      - Thread-safe operation
    """
    
    def __init__(
        self,
        bpm: float = 120.0,
        midi_port: str = "ClockMaster",
        click_wav: Optional[str] = None
    ):
        """
        Initialize the clock master system.
        
        Args:
            bpm: Initial tempo in beats per minute
            midi_port: Name of virtual MIDI output port
            click_wav: Path to WAV file for metronome click (optional)
        """
        self.metronome = MetronomeClick(wav_file=click_wav)
        self.midi = MIDIClockMaster(port_name=midi_port, bpm=bpm)
        
        # Register metronome.play() as the beat callback
        # This ensures audio plays immediately when MIDI beat occurs
        self.midi.on_beat = self.metronome.play
    
    def start(self) -> None:
        """Start MIDI clock (metronome plays via callback)."""
        self.midi.start()
    
    def stop(self) -> None:
        """Stop MIDI clock and any playing audio."""
        self.midi.stop()
    
    def set_bpm(self, bpm: float) -> None:
        """
        Change tempo at runtime.
        
        Args:
            bpm: New tempo in beats per minute
        """
        # Only MIDI clock needs BPM - metronome listens to MIDI beat flag
        self.midi.set_bpm(bpm)
    
    def get_bpm(self) -> float:
        """Return current tempo in BPM."""
        return self.midi.get_bpm()
    
    def set_click_enabled(self, enabled: bool) -> None:
        """Enable or disable metronome click sound."""
        self.metronome.set_enabled(enabled)
    
    def is_click_enabled(self) -> bool:
        """Return True if click sound is enabled."""
        return self.metronome.is_enabled()
    
    def is_running(self) -> bool:
        """Return True if clock is currently running."""
        return self.midi.is_running()
