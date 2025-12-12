#!/usr/bin/env python3
"""MIDI Clock Master and Metronome."""

import argparse
import sys
import signal
from midi_clock import MIDIClockMaster
from audio import generate_click_tone, play_click


def main():
    parser = argparse.ArgumentParser(description="MIDI Clock Master and Metronome")
    parser.add_argument('--bpm', type=float, default=120.0, help='Tempo in BPM')
    parser.add_argument('--no-click', action='store_true', help='Disable audio click')
    parser.add_argument('--no-start', action='store_true', help='Don\'t auto-start')
    
    args = parser.parse_args()
    
    if args.bpm < 1:
        print("Error: BPM must be at least 1")
        return 1
    
    try:
        print(f"Initializing MIDI Clock Master...")
        print(f"  BPM: {args.bpm}")
        
        # Create clock
        clock = MIDIClockMaster(bpm=args.bpm)
        
        # Setup audio callback if enabled
        if not args.no_click:
            click_tone = generate_click_tone()
            clock.on_beat = lambda: play_click(click_tone)
        
        # Signal handlers
        def signal_handler(sig, frame):
            print("\nShutting down...")
            clock.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Auto-start
        if not args.no_start:
            print("Starting clock...")
            clock.start()
            print("✓ Clock is running\n")
        
        print("Commands: start, stop, bpm <value>, status, quit\n")
        
        while True:
            try:
                cmd = input("> ").strip().lower()
                
                if cmd == "start":
                    if not clock._running:
                        clock.start()
                        print("Clock started")
                    else:
                        print("Clock already running")
                
                elif cmd == "stop":
                    if clock._running:
                        clock.stop()
                        print("Clock stopped")
                    else:
                        print("Clock already stopped")
                
                elif cmd.startswith("bpm "):
                    try:
                        new_bpm = float(cmd[4:].strip())
                        clock.bpm = new_bpm
                        print(f"BPM changed to {new_bpm}")
                    except ValueError:
                        print("Invalid BPM value")
                
                elif cmd == "status":
                    status = "running" if clock._running else "stopped"
                    print(f"Status: {status}, BPM: {clock.bpm}")
                
                elif cmd == "quit":
                    clock.stop()
                    print("Goodbye")
                    break
                
                elif cmd and cmd != "help":
                    print("Unknown command")
            
            except KeyboardInterrupt:
                clock.stop()
                print("\nGoodbye")
                break
            except EOFError:
                clock.stop()
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
