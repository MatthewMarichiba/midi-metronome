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
      ,/< or ./>  - Decrease/increase volume by 0.05
      bXXX<enter> - Set BPM to XXX (valid: 20-300, else abort)
      dX<enter>   - Set divisions to X (1-9, else abort)
      T           - Tap tempo (average up to 5 taps, update BPM)
      q           - Initiate quit (prompts for Y confirmation)
      other       - Ignored
    """
    
    def __init__(self):
        self.bpm = 60.0
        self.divisions = 1
        self.is_running = False
        self.audio_muted = False
        self.volume = 0.3
        self.tap_times = []
        self.last_tap_time = None
        self.TAP_RESET_THRESHOLD = 3.0  # Reset if gap > 2 seconds
        
        # Try to import readchar for non-blocking input
        try:
            import readchar
            self.readchar = readchar
            self.has_readchar = True
        except ImportError:
            print("Warning: readchar not installed. Keyboard UI may not work optimally.")
            print("Install with: pip install readchar")
            self.has_readchar = False
    
    def set_initial_state(self, bpm: float, divisions: int, is_running: bool = False, audio_muted: bool = False, volume: float = 0.3) -> None:
        """Set initial BPM, divisions, volume, and state from the clock."""
        self.bpm = bpm
        self.divisions = divisions
        self.is_running = is_running
        self.audio_muted = audio_muted
        self.volume = volume
    
    def run(self, on_command: Callable) -> bool:
        """Run the keyboard input loop."""
        print("Keyboard UI active. Press keys: S(tart) M(ute) -/= (tempo) [/] (tempo ±5) ,/. (vol) b/d (sequences) T(ap) q(uit)")
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
            
            # Skip escape sequences (arrow keys, function keys, etc.)
            if ch == '\x1b':
                # Read and discard the rest of the escape sequence
                try:
                    self.readchar.readchar()  # Read '['
                    self.readchar.readchar()  # Read the direction/key code
                except:
                    pass
                continue
            # Handle sequence modes
            if sequence_mode == 'bpm':
                if ch == '\r' or ch == '\n':
                    print()  # Newline after entry
                    # Complete BPM sequence
                    try:
                        bpm = float(sequence_buffer)
                        if 20 <= bpm <= 300:
                            on_command('set_bpm', bpm=bpm, divisions=self.divisions)
                            self.bpm = bpm
                        else:
                            print("BPM must be 20-300")
                    except ValueError:
                        print("Invalid BPM")
                    sequence_buffer = ""
                    sequence_mode = None
                elif ch.isdigit() or ch == '.':
                    sequence_buffer += ch
                    print(ch, end='', flush=True)  # Echo character
                elif ch == '\x7f':  # Backspace
                    if sequence_buffer:
                        sequence_buffer = sequence_buffer[:-1]
                        print('\b \b', end='', flush=True)  # Backspace display
                else:
                    print()  # Newline and abort
                    print("Aborted")
                    sequence_buffer = ""
                    sequence_mode = None
                continue
            
            elif sequence_mode == 'divisions':
                if ch.isdigit():
                    div = int(ch)
                    if 1 <= div <= 9:
                        on_command('set_bpm', bpm=self.bpm, divisions=div)
                        self.divisions = div
                    else:
                        print(f"Invalid division. Valid: 1-9")
                else:
                    print("Cancelled")
                sequence_mode = None
                continue
            
            elif sequence_mode == 'quit_confirm':
                if ch in ('y', 'Y'):
                    on_command('quit')
                    return True
                else:
                    print("Cancelled")
                    sequence_mode = None
                continue
            
            # Single keypress commands
            if ch == 's' or ch == 'S':
                if self.is_running:
                    on_command('stop')
                    self.is_running = False
                else:
                    on_command('start')
                    self.is_running = True
            
            elif ch == 'm' or ch == 'M':
                if self.audio_muted:
                    on_command('unmute_audio')
                    self.audio_muted = False
                else:
                    on_command('mute_audio')
                    self.audio_muted = True
            
            elif ch == '-' or ch == '_':
                new_bpm = max(20, self.bpm - 1)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
            
            elif ch == '=' or ch == '+':
                new_bpm = min(300, self.bpm + 1)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
            
            elif ch == '[' or ch == '{':
                # Round to nearest multiple of 5, then subtract 5
                rounded = round(self.bpm / 5) * 5
                new_bpm = max(20, rounded - 5)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
            
            elif ch == ']' or ch == '}':
                # Round to nearest multiple of 5, then add 5
                rounded = round(self.bpm / 5) * 5
                new_bpm = min(300, rounded + 5)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
            
            elif ch == ',' or ch == '<':
                new_volume = max(0.0, self.volume - 0.05)
                on_command('set_volume', volume=new_volume)
                self.volume = new_volume
            
            elif ch == '.' or ch == '>':
                new_volume = min(1.0, self.volume + 0.05)
                on_command('set_volume', volume=new_volume)
                self.volume = new_volume
            
            elif ch == 'b' or ch == 'B':
                sequence_buffer = ""
                sequence_mode = 'bpm'
                print("Enter BPM (20-300), then press Enter: ", end='', flush=True)
            
            elif ch == 'd' or ch == 'D':
                sequence_mode = 'divisions'
                print("Enter division (1-9): ", end='', flush=True)
            
            elif ch == 't' or ch == 'T':
                current_time = time.time()
                
                # Check if there's a long gap since last tap (reset if too long)
                if self.last_tap_time is not None:
                    gap = current_time - self.last_tap_time
                    if gap > self.TAP_RESET_THRESHOLD:
                        # Long gap detected, reset tap buffer
                        self.tap_times = []
                
                self.tap_times.append(current_time)
                self.last_tap_time = current_time
                
                # Keep only last 5 taps
                if len(self.tap_times) > 5:
                    self.tap_times = self.tap_times[-5:]
                
                if len(self.tap_times) > 1:
                    # Calculate average interval
                    intervals = [self.tap_times[i] - self.tap_times[i-1] 
                                for i in range(1, len(self.tap_times))]
                    avg_interval = sum(intervals) / len(intervals)
                    
                    # Convert interval to BPM (assumes taps are on the beat)
                    new_bpm = round(60.0 / avg_interval)
                    if 20 <= new_bpm <= 300:
                        on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                        self.bpm = new_bpm
            
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
