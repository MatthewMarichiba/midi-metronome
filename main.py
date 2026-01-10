#!/usr/bin/env python3
"""MIDI Clock Master and Metronome."""

import argparse
import sys
import signal
from midi_clock import MIDIClockMaster
from audio import generate_beat_pattern, play_click
from ui_legacy import LegacyLineUIController
from ui_keyboard import KeyboardUIController
from ui_midi import MIDIUIController


def main():
    parser = argparse.ArgumentParser(description="MIDI Clock Master and Metronome")
    parser.add_argument('-b', '--bpm', type=float, default=60.0, help='Tempo in BPM')
    parser.add_argument('-d', '--divisions', type=int, default=1, help='Division ticks per beat (default: 1)')
    parser.add_argument('-v', '--volume', type=float, default=0.3, help='Audio volume (0.0-1.0, default: 0.3)')
    parser.add_argument('-m', '--mute', action='store_true', help='Start with audio muted')
    parser.add_argument('--no-start', action='store_true', help='Don\'t auto-start')
    parser.add_argument('-t', '--target', type=str, default='HELIX', help='Target MIDI device to auto-connect to (default: HELIX)')
    parser.add_argument('--ui', type=str, choices=['legacy', 'keyboard', 'midi'], default='keyboard', help='UI mode (default: keyboard)')
    parser.add_argument('--midi-controller', type=str, default='Arturia', help='MIDI controller name to connect to (for --ui midi)')
    
    args = parser.parse_args()
    
    if args.bpm < 1:
        print("Error: BPM must be at least 1")
        return 1
    
    if not 0.0 <= args.volume <= 1.0:
        print("Error: Volume must be between 0.0 and 1.0")
        return 1
    
    try:
        print(f"Initializing MIDI Clock Master...")
        print(f"  BPM: {args.bpm}")
        
        # Setup audio - generate beat pattern with divisions
        current_volume = args.volume
        beat_pattern = generate_beat_pattern(divisions=args.divisions, bpm=args.bpm, volume=current_volume)
        beat_callback = lambda: play_click(beat_pattern)
        
        # Create clock with beat callback only (no division callback needed)
        clock = MIDIClockMaster(
            bpm=args.bpm, 
            target=args.target, 
            beat_callback=beat_callback, 
            divisions=args.divisions,
            audio_muted=args.mute
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
            ui.set_initial_state(args.bpm, args.divisions, is_running=not args.no_start, audio_muted=args.mute, volume=current_volume)
        elif args.ui == 'midi':
            ui = MIDIUIController(controller_name=args.midi_controller)
            ui.set_initial_state(args.bpm, args.divisions, is_running=not args.no_start, audio_muted=args.mute, volume=current_volume)
        else:
            ui = LegacyLineUIController()
        
        # Command dispatcher: translate UI commands to clock actions
        def handle_command(cmd: str, **kwargs):
            nonlocal beat_pattern, current_volume
            
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
                bpm = kwargs.get('bpm', 60.0)
                divisions = kwargs.get('divisions', 1)
                if bpm < 1:
                    print("BPM must be at least 1")
                else:
                    # Regenerate beat pattern if divisions or BPM changed
                    if divisions != clock.divisions or bpm != clock.bpm:
                        beat_pattern = generate_beat_pattern(divisions=divisions, bpm=bpm, volume=current_volume)
                        beat_callback = lambda: play_click(beat_pattern)
                        clock.on_beat = beat_callback
                    
                    clock.set_bpm(bpm, divisions)
                    print(f"BPM: {bpm}, Divisions: {divisions}")
            
            elif cmd == 'set_volume':
                volume = kwargs.get('volume', 0.3)
                volume = max(0.0, min(1.0, volume))  # Clamp to valid range
                current_volume = volume
                # Regenerate beat pattern with new volume
                beat_pattern = generate_beat_pattern(divisions=clock.divisions, bpm=clock.bpm, volume=current_volume)
                beat_callback = lambda: play_click(beat_pattern)
                clock.on_beat = beat_callback
                print(f"Volume: {volume:.2f}")
            
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
