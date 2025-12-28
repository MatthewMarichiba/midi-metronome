"""
Example configuration file for customizing MIDI controller mappings.

Copy this file and modify the CC numbers to match your MIDI controller.
Then import and use it in your own script or modify main.py to use it.
"""

from ui_midi import MIDIUIController

# Example 1: Custom CC mapping for a different controller
CUSTOM_CC_MAP = {
    'start_stop': 64,      # Toggle start/stop
    'mute': 65,            # Toggle mute/unmute
    'tap_tempo': 66,       # Tap tempo button
    'bpm_coarse': 1,       # Continuous CC for BPM (often modwheel)
    'bpm_fine_up': 67,     # Button: increase BPM by 1
    'bpm_fine_down': 68,   # Button: decrease BPM by 1
    'bpm_jump_up': 69,     # Button: increase BPM by 5
    'bpm_jump_down': 70,   # Button: decrease BPM by 5
    'divisions_up': 71,    # Button: increase divisions
    'divisions_down': 72,  # Button: decrease divisions
    'quit': 73,            # Quit button (requires double-press)
}

# Example 2: Minimal mapping (only essential controls)
MINIMAL_CC_MAP = {
    'start_stop': 20,
    'mute': 21,
    'tap_tempo': 22,
    'bpm_coarse': 23,
    'quit': 30,
}

# Example 3: Button-only mapping (no continuous CC)
BUTTON_ONLY_CC_MAP = {
    'start_stop': 20,
    'mute': 21,
    'tap_tempo': 22,
    'bpm_fine_up': 24,
    'bpm_fine_down': 25,
    'bpm_jump_up': 26,
    'bpm_jump_down': 27,
    'divisions_up': 28,
    'divisions_down': 29,
    'quit': 30,
}


def create_arturia_controller():
    """Create controller configured for Arturia devices."""
    return MIDIUIController(
        controller_name="Arturia",
        cc_map=None  # Use default mapping
    )


def create_custom_controller(controller_name="My MIDI Controller"):
    """Create controller with custom mapping."""
    return MIDIUIController(
        controller_name=controller_name,
        cc_map=CUSTOM_CC_MAP
    )


def create_minimal_controller(controller_name="Arturia"):
    """Create controller with minimal controls."""
    return MIDIUIController(
        controller_name=controller_name,
        cc_map=MINIMAL_CC_MAP
    )


if __name__ == "__main__":
    # Example usage
    print("MIDI Controller Configuration Examples")
    print("=" * 50)
    
    print("\nDefault CC Mapping:")
    controller = MIDIUIController()
    for cmd, cc in sorted(controller.cc_map.items(), key=lambda x: x[1]):
        print(f"  CC{cc:3d}: {cmd}")
    
    print("\nCustom CC Mapping:")
    for cmd, cc in sorted(CUSTOM_CC_MAP.items(), key=lambda x: x[1]):
        print(f"  CC{cc:3d}: {cmd}")
    
    print("\nMinimal CC Mapping:")
    for cmd, cc in sorted(MINIMAL_CC_MAP.items(), key=lambda x: x[1]):
        print(f"  CC{cc:3d}: {cmd}")
    
    print("\nButton-Only CC Mapping:")
    for cmd, cc in sorted(BUTTON_ONLY_CC_MAP.items(), key=lambda x: x[1]):
        print(f"  CC{cc:3d}: {cmd}")
