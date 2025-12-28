"""MIDI controller-based UI controller."""

import rtmidi
import time
from interval_timer import IntervalTimer
from ui_controller import UIController
from typing import Callable, Optional, Dict, Any


class MIDIUIController(UIController):
    """
    MIDI controller interface that responds to MIDI CC messages.
    
    Highly configurable with mappable CC numbers for different commands.
    Supports both button-style CC (0/127 values) and continuous CC values.
    """
    
    # Default CC mapping configuration
    DEFAULT_CC_MAP = {
        'start_stop': 20,      # Toggle start/stop
        'mute': 21,            # Toggle mute/unmute
        'tap_tempo': 22,       # Tap tempo button
        'bpm_coarse': 23,      # Continuous CC for BPM (coarse)
        'bpm_fine_up': 24,     # Button: increase BPM by 1
        'bpm_fine_down': 25,   # Button: decrease BPM by 1
        'bpm_jump_up': 26,     # Button: increase BPM by 5
        'bpm_jump_down': 27,   # Button: decrease BPM by 5
        'divisions_up': 28,    # Button: increase divisions
        'divisions_down': 29,  # Button: decrease divisions
        'quit': 30,            # Quit button (requires double-press)
    }
    
    def __init__(self, 
                 controller_name: str = "Arturia",
                 cc_map: Optional[Dict[str, int]] = None,
                 bpm_range: tuple = (20.0, 300.0),
                 divisions_range: tuple = (1, 9)):
        """
        Initialize MIDI UI Controller.
        
        Args:
            controller_name: Substring to match MIDI input device name (e.g., "Arturia")
            cc_map: Custom CC mapping dictionary. If None, uses DEFAULT_CC_MAP
            bpm_range: Tuple of (min_bpm, max_bpm)
            divisions_range: Tuple of (min_divisions, max_divisions)
        """
        self.controller_name = controller_name
        self.cc_map = cc_map if cc_map is not None else self.DEFAULT_CC_MAP.copy()
        self.bpm_range = bpm_range
        self.divisions_range = divisions_range
        
        # State tracking
        self.bpm = 120.0
        self.divisions = 1
        self.is_running = False
        self.audio_muted = False
        
        # Tap tempo state
        self.tap_times = []
        self.last_tap_time = None
        self.TAP_RESET_THRESHOLD = 3.0
        
        # Quit confirmation (double-press within 2 seconds)
        self.quit_press_time = None
        self.QUIT_CONFIRM_WINDOW = 2.0
        
        # MIDI input
        self.midiin: Optional[rtmidi.MidiIn] = None
        self._running = False
        
        # Create reverse lookup for CC numbers to command names
        self._cc_to_command = {v: k for k, v in self.cc_map.items()}
    
    def set_initial_state(self, bpm: float, divisions: int, 
                         is_running: bool = False, audio_muted: bool = False) -> None:
        """Set initial BPM, divisions, and state from the clock."""
        self.bpm = bpm
        self.divisions = divisions
        self.is_running = is_running
        self.audio_muted = audio_muted
    
    def _find_controller_port(self) -> Optional[int]:
        """Find MIDI input port matching controller_name."""
        midiin = rtmidi.MidiIn()
        ports = midiin.get_ports()
        
        for i, port_name in enumerate(ports):
            if self.controller_name.lower() in port_name.lower():
                print(f"Found MIDI controller: {port_name}")
                return i
        
        return None
    
    def _open_midi_input(self) -> bool:
        """Open MIDI input port."""
        try:
            self.midiin = rtmidi.MidiIn()
            port_idx = self._find_controller_port()
            
            if port_idx is None:
                print(f"Error: Could not find MIDI controller matching '{self.controller_name}'")
                print("Available MIDI inputs:")
                for i, port in enumerate(self.midiin.get_ports()):
                    print(f"  {i}: {port}")
                return False
            
            self.midiin.open_port(port_idx)
            print(f"✓ MIDI controller connected")
            return True
            
        except Exception as e:
            print(f"Error opening MIDI input: {e}")
            return False
    
    def _handle_tap_tempo(self, on_command: Callable) -> None:
        """Process tap tempo and calculate average BPM."""
        current_time = time.time()
        
        # Reset if too much time has passed
        if self.last_tap_time and (current_time - self.last_tap_time) > self.TAP_RESET_THRESHOLD:
            self.tap_times = []
        
        self.tap_times.append(current_time)
        self.last_tap_time = current_time
        
        # Keep only last 5 taps
        if len(self.tap_times) > 5:
            self.tap_times.pop(0)
        
        # Need at least 2 taps to calculate tempo
        if len(self.tap_times) >= 2:
            intervals = []
            for i in range(1, len(self.tap_times)):
                intervals.append(self.tap_times[i] - self.tap_times[i-1])
            
            avg_interval = sum(intervals) / len(intervals)
            bpm = 60.0 / avg_interval
            
            # Clamp to valid range
            bpm = max(self.bpm_range[0], min(self.bpm_range[1], bpm))
            
            on_command('set_bpm', bpm=bpm, divisions=self.divisions)
            self.bpm = bpm
            print(f"Tap tempo: {bpm:.1f} BPM (from {len(self.tap_times)} taps)")
    
    def _handle_cc_message(self, cc_num: int, value: int, on_command: Callable) -> bool:
        """
        Handle incoming CC message.
        
        Returns True if quit was triggered, False otherwise.
        """
        # Look up command name from CC number
        cmd_name = self._cc_to_command.get(cc_num)
        
        if cmd_name is None:
            return False  # Ignore unmapped CC
        
        # Button-style CCs (respond to value >= 64, ignore release)
        button_threshold = 64
        
        if cmd_name == 'start_stop':
            if value >= button_threshold:
                if self.is_running:
                    on_command('stop')
                    self.is_running = False
                else:
                    on_command('start')
                    self.is_running = True
        
        elif cmd_name == 'mute':
            if value >= button_threshold:
                if self.audio_muted:
                    on_command('unmute_audio')
                    self.audio_muted = False
                else:
                    on_command('mute_audio')
                    self.audio_muted = True
        
        elif cmd_name == 'tap_tempo':
            if value >= button_threshold:
                self._handle_tap_tempo(on_command)
        
        elif cmd_name == 'bpm_coarse':
            # Continuous CC: map 0-127 to BPM range
            min_bpm, max_bpm = self.bpm_range
            bpm = min_bpm + (value / 127.0) * (max_bpm - min_bpm)
            on_command('set_bpm', bpm=bpm, divisions=self.divisions)
            self.bpm = bpm
        
        elif cmd_name == 'bpm_fine_up':
            if value >= button_threshold:
                new_bpm = min(self.bpm_range[1], self.bpm + 1)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
        
        elif cmd_name == 'bpm_fine_down':
            if value >= button_threshold:
                new_bpm = max(self.bpm_range[0], self.bpm - 1)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
        
        elif cmd_name == 'bpm_jump_up':
            if value >= button_threshold:
                new_bpm = min(self.bpm_range[1], self.bpm + 5)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
        
        elif cmd_name == 'bpm_jump_down':
            if value >= button_threshold:
                new_bpm = max(self.bpm_range[0], self.bpm - 5)
                on_command('set_bpm', bpm=new_bpm, divisions=self.divisions)
                self.bpm = new_bpm
        
        elif cmd_name == 'divisions_up':
            if value >= button_threshold:
                new_div = min(self.divisions_range[1], self.divisions + 1)
                on_command('set_bpm', bpm=self.bpm, divisions=new_div)
                self.divisions = new_div
        
        elif cmd_name == 'divisions_down':
            if value >= button_threshold:
                new_div = max(self.divisions_range[0], self.divisions - 1)
                on_command('set_bpm', bpm=self.bpm, divisions=new_div)
                self.divisions = new_div
        
        elif cmd_name == 'quit':
            if value >= button_threshold:
                current_time = time.time()
                if (self.quit_press_time and 
                    current_time - self.quit_press_time < self.QUIT_CONFIRM_WINDOW):
                    # Double-press confirmed
                    print("\nQuitting...")
                    on_command('quit')
                    return True
                else:
                    # First press
                    print("Press quit again to confirm...")
                    self.quit_press_time = current_time
        
        return False
    
    def _print_cc_mapping(self) -> None:
        """Print the current CC mapping for user reference."""
        print("\nMIDI CC Mapping:")
        print("-" * 40)
        for cmd_name, cc_num in sorted(self.cc_map.items(), key=lambda x: x[1]):
            print(f"  CC{cc_num:3d}: {cmd_name}")
        print("-" * 40)
    
    def run(self, on_command: Callable) -> bool:
        """Run the MIDI input loop."""
        print(f"MIDI UI active. Listening for controller: {self.controller_name}")
        
        if not self._open_midi_input():
            return False
        
        self._print_cc_mapping()
        print("\nReady. Use your MIDI controller to control the metronome.")
        print("(Press Ctrl+C to quit)\n")
        
        self._running = True
        
        try:
            # Poll for MIDI messages at ~24Hz (slightly faster than MIDI time pulses)
            timer = IntervalTimer(period=0.04)
            
            for _ in timer:
                if not self._running:
                    break
                
                # Drain all queued messages this interval
                while True:
                    msg = self.midiin.get_message()
                    
                    if not msg:  # No more messages in queue
                        break
                    
                    message, deltatime = msg
                    
                    # Check if it's a CC message (status byte 0xB0-0xBF)
                    if len(message) >= 3 and (message[0] & 0xF0) == 0xB0:
                        cc_num = message[1]
                        cc_value = message[2]
                        
                        # Handle the CC message
                        should_quit = self._handle_cc_message(cc_num, cc_value, on_command)
                        if should_quit:
                            self._running = False
                            return True
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            on_command('quit')
            return True
        
        except Exception as e:
            print(f"Error in MIDI UI: {e}")
            return False
        
        finally:
            if self.midiin:
                self.midiin.close_port()
                print("MIDI controller disconnected")
        
        return True


# Example of creating a controller with custom CC mapping
def create_custom_midi_controller(controller_name: str = "Arturia", 
                                 custom_mapping: Optional[Dict[str, int]] = None) -> MIDIUIController:
    """
    Factory function to create MIDI controller with optional custom mapping.
    
    Example usage:
        # Use default mapping
        controller = create_custom_midi_controller("Arturia")
        
        # Or with custom mapping
        custom_map = {
            'start_stop': 64,
            'mute': 65,
            'tap_tempo': 66,
            'bpm_fine_up': 67,
            'bpm_fine_down': 68,
        }
        controller = create_custom_midi_controller("Arturia", custom_map)
    """
    return MIDIUIController(controller_name=controller_name, cc_map=custom_mapping)
