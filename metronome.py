"""
Metronome Audio Click Module

This module handles playback of click sounds triggered by MIDI clock beats.
The metronome is called directly from the MIDI clock's beat callback,
ensuring zero polling latency.

Key concepts:
  - Called directly on beat boundaries from MIDI clock (every 24 MIDI clocks)
  - Plays audio immediately via subprocess (aplay/ffplay)
  - No independent timing or threads
  - Uses subprocess to avoid audio library threading issues
  - Stays perfectly in sync with MIDI clock output
  - Designed for Raspberry Pi compatibility
"""

import subprocess
import threading
import os
from typing import Optional


class MetronomeClick:
    """
    Manages metronome click sound playback triggered by MIDI clock beats.
    
    This class plays audio immediately when called from the MIDI clock's
    beat callback, ensuring minimal and consistent latency.
    """
    
    def __init__(self, wav_file: Optional[str] = None):
        """
        Initialize the metronome click sound.
        
        Args:
            wav_file: Path to WAV file for click sound.
                     If None, no audio will be played (useful for testing).
        """
        self.wav_file = wav_file
        self._lock = threading.RLock()
        self.enabled = True
        self._last_play_process: Optional[subprocess.Popen] = None
        
        # Check which audio player is available
        self.audio_player = self._find_audio_player()
        
        if wav_file:
            self._validate_audio_file()
    
    def _find_audio_player(self) -> Optional[str]:
        """Find available audio player: aplay, ffplay, or paplay."""
        for player in ['aplay', 'ffplay', 'paplay']:
            result = subprocess.run(['which', player], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=1)
            if result.returncode == 0:
                print(f"Using audio player: {player}")
                return player
        print("Warning: No audio player found (aplay, ffplay, or paplay)")
        return None
    
    def _validate_audio_file(self) -> None:
        """Validate that WAV file exists and is readable."""
        if not self.wav_file or not os.path.exists(self.wav_file):
            print(f"Warning: WAV file not found: {self.wav_file}")
            self.wav_file = None
            return
        
        print(f"Loaded click audio: {self.wav_file}")
    
    def play(self) -> None:
        """
        Trigger click sound playback immediately.
        
        Called directly from MIDI clock beat callback.
        Uses subprocess to invoke aplay/ffplay to avoid audio library issues.
        
        Note: This runs in the MIDI clock's thread for minimal latency.
        """
        if not self.enabled or not self.wav_file or not self.audio_player:
            return
        
        with self._lock:
            try:
                # Terminate previous playback if still running
                if self._last_play_process:
                    try:
                        self._last_play_process.terminate()
                        self._last_play_process.wait(timeout=0.1)
                    except:
                        try:
                            self._last_play_process.kill()
                        except:
                            pass
                
                # Play audio file via subprocess
                if self.audio_player == 'ffplay':
                    # ffplay -nodisp -autoexit suppresses GUI and exits after playing
                    self._last_play_process = subprocess.Popen(
                        ['ffplay', '-nodisp', '-autoexit', self.wav_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    # aplay/paplay - just play and let it finish
                    self._last_play_process = subprocess.Popen(
                        [self.audio_player, self.wav_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
            except Exception as e:
                print(f"Error playing click sound: {e}")
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable click sound playback."""
        with self._lock:
            self.enabled = enabled
    
    def is_enabled(self) -> bool:
        """Return True if click sound is enabled."""
        with self._lock:
            return self.enabled
