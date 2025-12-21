"""Single-keypress keyboard UI controller."""

import time
from ui_controller import UIController
from typing import Callable, Optional
import sys


class KeyboardUIController(UIController):
    """
    Single-keypress keyboard interface with state machine for sequences.
    
    Commands:
      S           - Start/stop MIDI clock
      M           - Mute/unmute audio click
      -/_ or =/+  - Decrease/increase tempo by 1 BPM
      [/{ or ]/}  - Decrease/increase tempo by 5 BPM
      bXXX<enter> - Set BPM to XXX (valid: 20-300, else abort)
      dX<enter>   - Set divisions to X (1-9, else abort)
      T           - Tap tempo (average up to 5 taps, update BPM)
      q           - Initiate quit (prompts for Y confirmation)
      other       - Ignored
    """
    
    def __init__(self):
        self.bpm = 120.0
        self.divisions = 1
        self.is_running = False
        self.audio_muted = False
        self.tap_times = []
        
        # Try to import readchar for non-blocking input
        try:
            import readchar
            self.readchar = readchar
            self.has_readchar = True
        except ImportError:
            print("Warning: readchar not installed. Keyboard UI may not work optimally.")
            print("Install with: pip install readchar")
            self.has_readchar = False
    
    def run(self, on_command: Callable) -> bool:
        """Run the keyboard input loop."""
        print("Keyboard UI active. Press keys: S(tart) M(ute) -/= (tempo) [/] (tempo ±5) b/d (sequences) T(ap) q(uit)")
        print()
        
        if not self.has_readchar:
            print("Falling back to line input (readchar not available)")
            return self._run_line_based(on_command)
        
        try:
            return self._run_keypress_based(on_command)
        except KeyboardInterrupt:
            on_command('quit')
            print("\nGoodbye")
            return True
        except Exception as e:
            print(f"Error in keyboard UI: {e}")
            return False
    
    def _run_keypress_based(self, on_command: Callable) -> bool:
        """Run with actual single-keypress input."""
        sequence_buffer = ""
        sequence_mode = None  # 'bpm', 'divisions', or None
        
        while True:
            try:
                ch = self.readchar.readchar()
            except KeyboardInterrupt:
                on_command('quit')
                print("\nGoodbye")
                return True
            
            # Handle sequence modes
            if sequence_mode == 'bpm':
                if ch == '\r' or ch == '\n':
                    # Complete BPM sequence
                    try:
                        bpm = float(sequence_buffer)
                        if 20 <= bpm <= 300:
                            on_command('set_bpm', bpm=bpm, divisions=self.divisions)
                            self.bpm = bpm
                            print(f"BPM: {bpm}")
                        else:
                            print("BPM must be 20-300")
                    except ValueError:
                        print("Invalid BPM")
                    sequence_buffer = ""
                    sequence_mode = None
                elif ch.isdigit() or ch == '.':
                    sequence_buffer += ch
                elif ch == '\x7f':  # Backspace
                    sequence_buffer = sequence_buffer[:-1]
                else:
                    print("Aborted")
                    sequence_buffer = ""
                    sequence_mode = None
                continue
            
            elif sequence_mode == 'divisions':
                if ch == '\r' or ch == '\n':
                    # Complete divisions sequence
                    try:
                        div = int(sequence_buffer)
                        if 1 <= div <= 9:
                            on_command('set_bpm', bpm=self.bpm, divisions=div)
                            self.divisions = div
                            print(f"Divisions: {div}")
                        else:
                            print("Divisions must be 1-9")
                    except ValueError:
                        print("Invalid divisions")
                    sequence_buffer = ""
                    sequence_mode = None
                elif ch.isdigit():
                    sequence_buffer += ch
                elif ch == '\x7f':  # Backspace
                    sequence_buffer = sequence_buffer[:-1]
                else:
                    print("Aborted")
                    sequence_buffer = ""
                    sequence_mode = None
                continue
            
            elif sequence_mode == 'quit_confirm':
                if ch in ('y', 'Y'):
                    on_command('quit')
                    print("Goodbye")
                    return True
                elif ch in ('n', 'N') or ch == '\x1b':  # ESC
                    print("Quit cancelled")
                    sequence_mode = None
                else:
                    print("Invalid. Press Y to confirm quit, N to cancel")
                continue
            
            # Single keypress commands
            if ch == 's' or ch == 'S':
                if self.is_running:
                    on_command('stop')
                    self.is_running = False
                    print("Clock stopped")
                else:
                    on_command('start')
                    self.is_running = True
                    print("Clock started")
            
            elif ch == 'm' or ch == 'M':
                if self.audio_muted:
                    on_command('unmute_audio')
                    self.audio_muted = False
                    print("Audio unmuted")
                else:
                    on_command('mute_audio')
                    self.audio_muted = True
                    print("Audio muted")
            
            elif ch == '-' or ch == '_':
                new_bpm = max(1, self.bpm - 1)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
                print(f"BPM: {new_bpm}")
            
            elif ch == '=' or ch == '+':
                new_bpm = self.bpm + 1
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
                print(f"BPM: {new_bpm}")
            
            elif ch == '[' or ch == '{':
                new_bpm = max(1, self.bpm - 5)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
                print(f"BPM: {new_bpm}")
            
            elif ch == ']' or ch == '}':
                new_bpm = self.bpm + 5
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
                print(f"BPM: {new_bpm}")
            
            elif ch == 'b' or ch == 'B':
                sequence_buffer = ""
                sequence_mode = 'bpm'
                print("Enter BPM (20-300), then press Enter: ", end='', flush=True)
            
            elif ch == 'd' or ch == 'D':
                sequence_buffer = ""
                sequence_mode = 'divisions'
                print("Enter divisions (1-9), then press Enter: ", end='', flush=True)
            
            elif ch == 't' or ch == 'T':
                current_time = time.time()
                self.tap_times.append(current_time)
                
                # Keep only last 5 taps
                if len(self.tap_times) > 5:
                    self.tap_times = self.tap_times[-5:]
                
                if len(self.tap_times) > 1:
                    # Calculate average interval
                    intervals = [self.tap_times[i] - self.tap_times[i-1] 
                                for i in range(1, len(self.tap_times))]
                    avg_interval = sum(intervals) / len(intervals)
                    
                    # Convert interval to BPM (assumes taps are on the beat)
                    new_bpm = 60.0 / avg_interval
                    if 20 <= new_bpm <= 300:
                        on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                        self.bpm = new_bpm
                        print(f"Tap tempo: {new_bpm:.1f} BPM ({len(self.tap_times)} taps)")
                    else:
                        print(f"Tap tempo out of range: {new_bpm:.1f} BPM")
                else:
                    print("Tap tempo: tap again to calculate")
            
            elif ch == 'q' or ch == 'Q':
                sequence_mode = 'quit_confirm'
                print("Press Y to confirm quit, N to cancel: ", end='', flush=True)
            
            # Ignore other keys
    
    def _run_line_based(self, on_command: Callable) -> bool:
        """Fallback line-based input when readchar not available."""
        print("Using line-based input. Type 's', 'm', 'b BPM', 'q', etc.")
        
        while True:
            try:
                line = input("> ").strip()
                if not line:
                    continue
                
                ch = line[0].lower()
                
                if ch == 's':
                    if self.is_running:
                        on_command('stop')
                        self.is_running = False
                    else:
                        on_command('start')
                        self.is_running = True
                
                elif ch == 'm':
                    if self.audio_muted:
                        on_command('unmute_audio')
                        self.audio_muted = False
                    else:
                        on_command('mute_audio')
                        self.audio_muted = True
                
                elif ch == 'b' and len(line) > 1:
                    try:
                        bpm = float(line[1:].strip())
                        if 20 <= bpm <= 300:
                            on_command('set_bpm', bpm=bpm, divisions=self.divisions)
                            self.bpm = bpm
                        else:
                            print("BPM must be 20-300")
                    except ValueError:
                        print("Invalid BPM")
                
                elif ch == 'q':
                    on_command('quit')
                    print("Goodbye")
                    return True
                
                elif ch == '-':
                    new_bpm = max(1, self.bpm - 1)
                    on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                    self.bpm = new_bpm
                
                elif ch == '+' or ch == '=':
                    new_bpm = self.bpm + 1
                    on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                    self.bpm = new_bpm
            
            except KeyboardInterrupt:
                on_command('quit')
                print("\nGoodbye")
                return True
            except EOFError:
                on_command('quit')
                print("\nGoodbye")
                return True
