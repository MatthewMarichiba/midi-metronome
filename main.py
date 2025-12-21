#!/usr/bin/env python3
"""MIDI Clock Master and Metronome."""

import argparse
import sys
import signal
from midi_clock import MIDIClockMaster
from audio import generate_click_tone, generate_division_tone, play_click
from ui_legacy import LegacyLineUIController
from ui_keyboard import KeyboardUIController


def main():
    parser = argparse.ArgumentParser(description="MIDI Clock Master and Metronome")
    parser.add_argument('-b', '--bpm', type=float, default=120.0, help='Tempo in BPM')
    parser.add_argument('-d', '--divisions', type=int, default=1, help='Division ticks per beat (default: 1)')
    parser.add_argument('-m', '--mute', action='store_true', help='Start with audio muted')
    parser.add_argument('--no-start', action='store_true', help='Don\'t auto-start')
    parser.add_argument('-t', '--target', type=str, default='HELIX', help='Target MIDI device to auto-connect to (default: HELIX)')
    parser.add_argument('--ui', type=str, choices=['legacy', 'keyboard'], default='keyboard', help='UI mode (default: keyboard)')
    
    args = parser.parse_args()
    
    if args.bpm < 1:
        print("Error: BPM must be at least 1")
        return 1
    
    try:
        print(f"Initializing MIDI Clock Master...")
        print(f"  BPM: {args.bpm}")
        
        # Setup audio tones
        click_tone = generate_click_tone()
        division_tone = generate_division_tone()
        
        # Create callbacks
        def beat_click():
            play_click(click_tone)
        
        def div_click():
            if division_tone is not None:
                play_click(division_tone)
        
        # Create clock with callbacks
        clock = MIDIClockMaster(
            bpm=args.bpm, 
            target=args.target, 
            beat_callback=beat_click, 
            division_callback=div_click, 
            divisions=args.divisions,
            audio_muted=args.mute,
            auto_start=not args.no_start
        )
        
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
        else:
            print(f"  Audio: {'Muted' if args.mute else 'Enabled'} (divisions: {args.divisions})\n")
        
        # Select UI controller
        if args.ui == 'keyboard':
            ui = KeyboardUIController()
            ui.set_initial_state(args.bpm, args.divisions, is_running=not args.no_start, audio_muted=args.mute)
        else:
            ui = LegacyLineUIController()
        
        # Command dispatcher: translate UI commands to clock actions
        def handle_command(cmd: str, **kwargs):
            if cmd == 'start':
                if not clock._running:
                    clock.start()
                    print("Clock started")
                else:
                    print("Clock already running")
            
            elif cmd == 'stop':
                if clock._running:
                    clock.stop()
                    print("Clock stopped")
                else:
                    print("Clock already stopped")
            
            elif cmd == 'set_bpm':
                bpm = kwargs.get('bpm', 120.0)
                divisions = kwargs.get('divisions', 1)
                if bpm < 1:
                    print("BPM must be at least 1")
                else:
                    clock.set_bpm(bpm, divisions)
                    print(f"BPM: {bpm}, Divisions: {divisions}")
            
            elif cmd == 'mute_audio':
                clock.mute_audio()
                print("Audio muted")
            elif cmd == 'unmute_audio':
                clock.unmute_audio()
                print("Audio unmuted")
            
            elif cmd == 'status':
                status = "running" if clock._running else "stopped"
                print(f"Status: {status}, BPM: {clock.bpm}, Divisions: {clock.divisions}")
            
            elif cmd == 'quit':
                clock.stop()
        
        # Run the UI controller
        ui.run(on_command=handle_command)
        
        print("Goodbye")
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
