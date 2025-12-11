#!/usr/bin/env python3
"""
Diagnostic: Check MIDI clock timing
"""

import time
from midi_clock import MIDIClockMaster

def test_clock_timing():
    """Verify MIDI clock is sending messages at the right rate."""
    
    print("MIDI Clock Timing Diagnostic")
    print("=" * 60)
    
    midi = MIDIClockMaster(port_name="DiagTest", bpm=120.0)
    
    print(f"BPM: {midi.get_bpm()}")
    print(f"Expected interval per clock: {60 / (120 * 24):.6f} seconds")
    print(f"Expected clocks per second: {120 * 24 / 60}")
    print()
    
    # Start and check clock count over time
    midi.start()
    
    times = []
    counts = []
    
    for i in range(10):
        time.sleep(0.1)
        counts.append(midi.clock_count)
        times.append((i + 1) * 0.1)  # Start from 0.1, not 0
        elapsed = times[-1]
        rate = counts[-1] / elapsed if elapsed > 0 else 0
        print(f"  t={elapsed:.1f}s: clock_count={counts[-1]:3d}, rate={rate:6.1f} clocks/sec")
    
    midi.stop()
    
    print()
    print(f"Final clock count: {midi.clock_count}")
    print(f"Expected after 1 second: ~48")
    print(f"Clock rate: {midi.clock_count:.1f} clocks/sec")
    
    if midi.clock_count > 40:
        print("✓ Clock timing is correct")
    else:
        print("✗ Clock is running too slowly")

if __name__ == '__main__':
    test_clock_timing()
