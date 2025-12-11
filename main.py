#!/usr/bin/env python3
"""
MIDI Clock Master and Metronome - Main Entry Point

This script demonstrates the complete MIDI clock master system:
  1. Creates a virtual MIDI output port named "ClockMaster"
  2. Initializes MIDI realtime message generation
  3. Optionally plays synchronized audio click
  4. Starts the clock immediately (use --no-start to delay)
  5. Provides interactive control: start, stop, tempo changes

The system is designed to act as the sole clock master, with external
devices (Boomerang III, Helix Floor) acting as slaves listening to the
MIDI clock for precise quantization.

Usage:
    python3 main.py [--bpm BPM] [--click WAVFILE] [--no-click] [--no-start]

Examples:
    python3 main.py --bpm 100
    python3 main.py --click /path/to/click.wav
    python3 main.py --bpm 140 --click click.wav
    python3 main.py --no-start
    python3 main.py --no-click --no-start
"""

import argparse
import sys
import signal
import os
from clock_master import ClockMaster


def create_sample_click_wav():
    """
    Create a simple click sound WAV file for testing.
    Requires simpleaudio and numpy.
    """
    try:
        import numpy as np
        import wave
        
        sample_rate = 44100
        duration = 0.05  # 50ms click
        frequency = 800  # 800 Hz tone
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        samples = (0.3 * np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        
        # Write WAV file
        filename = "click.wav"
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(samples.tobytes())
        
        print(f"Created sample click sound: {filename}")
        return filename
    except ImportError:
        print("Warning: numpy required to generate sample click sound")
        print("Please provide a WAV file with --click option")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="MIDI Clock Master and Metronome",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py --bpm 100
  python3 main.py --click click.wav --bpm 120
  python3 main.py --no-click
        """
    )
    
    parser.add_argument(
        '--bpm',
        type=float,
        default=120.0,
        help='Initial tempo in beats per minute (default: 120)'
    )
    parser.add_argument(
        '--click',
        type=str,
        default=None,
        help='Path to WAV file for metronome click'
    )
    parser.add_argument(
        '--no-click',
        action='store_true',
        help='Disable metronome click sound'
    )
    parser.add_argument(
        '--port',
        type=str,
        default='ClockMaster',
        help='Name of MIDI virtual output port (default: ClockMaster)'
    )
    parser.add_argument(
        '--no-start',
        action='store_true',
        help='Do not auto-start the clock (wait for "start" command)'
    )
    
    args = parser.parse_args()
    
    # Validate BPM
    if args.bpm < 1:
        print("Error: BPM must be at least 1")
        return 1
    
    # Determine click file
    click_file = None
    if not args.no_click:
        if args.click:
            if not os.path.exists(args.click):
                print(f"Error: Click WAV file not found: {args.click}")
                return 1
            click_file = args.click
        else:
            # Try to create sample click
            click_file = create_sample_click_wav()
    
    try:
        # Initialize clock master
        print(f"Initializing MIDI Clock Master...")
        print(f"  Port: {args.port}")
        print(f"  BPM: {args.bpm}")
        if click_file:
            print(f"  Click: {click_file}")
        else:
            print(f"  Click: disabled")
        
        master = ClockMaster(
            bpm=args.bpm,
            midi_port=args.port,
            click_wav=click_file
        )
        
        # Set up signal handlers for clean shutdown
        def signal_handler(sig, frame):
            print("\nShutting down...")
            master.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Auto-start the clock unless --no-start is specified
        if not args.no_start:
            print("\nStarting clock...")
            master.start()
            print("✓ Clock is running")
        
        # Interactive control loop
        print("\nClock Master ready. Commands:")
        print("  start              - Start clock and metronome")
        print("  stop               - Stop clock and metronome")
        print("  bpm <value>        - Set tempo (e.g., 'bpm 140')")
        print("  click on/off       - Enable/disable click sound")
        print("  status             - Show current settings")
        print("  quit               - Exit")
        print()
        
        while True:
            try:
                cmd = input("> ").strip().lower()
                
                if cmd == "start":
                    if not master.is_running():
                        master.start()
                        print("Clock started")
                    else:
                        print("Clock already running")
                
                elif cmd == "stop":
                    if master.is_running():
                        master.stop()
                        print("Clock stopped")
                    else:
                        print("Clock already stopped")
                
                elif cmd.startswith("bpm "):
                    try:
                        new_bpm = float(cmd[4:].strip())
                        master.set_bpm(new_bpm)
                        print(f"BPM changed to {new_bpm}")
                    except ValueError:
                        print("Invalid BPM value")
                
                elif cmd == "click on":
                    master.set_click_enabled(True)
                    print("Click enabled")
                
                elif cmd == "click off":
                    master.set_click_enabled(False)
                    print("Click disabled")
                
                elif cmd == "status":
                    status = "running" if master.is_running() else "stopped"
                    click_status = "enabled" if master.is_click_enabled() else "disabled"
                    print(f"Status: {status}")
                    print(f"BPM: {master.get_bpm()}")
                    print(f"Click: {click_status}")
                
                elif cmd == "quit":
                    master.stop()
                    print("Goodbye")
                    break
                
                elif cmd == "help":
                    print("Commands: start, stop, bpm <value>, click on/off, status, quit")
                
                elif cmd != "":
                    print("Unknown command. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                master.stop()
                print("\nGoodbye")
                break
            except EOFError:
                master.stop()
                print("\nGoodbye")
                break
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
