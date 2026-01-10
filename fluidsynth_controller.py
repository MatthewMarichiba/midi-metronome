"""
FluidSynth Soundfont Controller - Change patches via keyboard.

Start FluidSynth before running this program:

$ fluidsynth -a alsa -m alsa_seq \
  -s \
  -z 256 \
  -c 2 \
  -r 44100 \
  -o synth.polyphony=32 \
  -o synth.reverb.active=no \
  -o synth.chorus.active=no \
  -o synth.cpu-cores=4 \
  -o audio.period-size=512 \
  -o audio.periods=2

  Then run this script:
  $ python3 fluidsynth_controller.py 

  Make sure a 
"""

import socket
import time
import sys
import os
import tty
import termios
from pathlib import Path
from typing import List


class FluidSynthController:
    """
    Control FluidSynth soundfonts via keyboard input.
    
    Connects to FluidSynth's TCP server and dynamically loads/unloads
    soundfonts to minimize RAM usage (ideal for Raspberry Pi).
    """
    
    def __init__(self, 
                 soundfonts: List[str],
                 fluidsynth_host: str = "localhost",
                 fluidsynth_port: int = 9800,
                 midi_channel: int = 1):
        """
        Initialize FluidSynth controller.
        
        Args:
            soundfonts: List of paths to .sf2/.sf3 files
            fluidsynth_host: FluidSynth server hostname
            fluidsynth_port: FluidSynth server port (default 9800)
            midi_channel: MIDI channel to assign soundfonts to (1-16)
        """
        self.soundfonts = soundfonts
        self.fluidsynth_host = fluidsynth_host
        self.fluidsynth_port = fluidsynth_port
        self.midi_channel = midi_channel
        self.running = False
        self.current_index = 0
        self.current_sf_id = None
        self.last_loaded_id = None  # Track last successful load for cleanup
        self.current_program = 0  # Track current program number
        self.current_bank = 0  # Track current bank number
        self.available_presets = []  # List of (bank, program, name) tuples
        self.preset_index = 0  # Index into available_presets
        
        # Connect to FluidSynth
        self._connect_fluidsynth()
        
        # Clean up any loaded soundfonts except ID 1 (FluidSynth default)
        self._cleanup_initial_soundfonts()
        
        # Load first soundfont
        self._load_soundfont(0)
        
    def _connect_fluidsynth(self):
        """Connect to FluidSynth TCP server."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.fluidsynth_host, self.fluidsynth_port))
            print(f"Connected to FluidSynth at {self.fluidsynth_host}:{self.fluidsynth_port}")
            # Read initial prompt
            self.sock.recv(4096)
        except Exception as e:
            raise ConnectionError(f"Could not connect to FluidSynth server: {e}\n"
                                f"Make sure FluidSynth is running with -s flag")
    
    def _cleanup_initial_soundfonts(self):
        """Unload all soundfonts except ID 1 on startup."""
        print("Cleaning up initial soundfonts...")
        fonts_response = self._send_command("fonts")
        
        # Parse loaded soundfont IDs
        for line in fonts_response.split('\n'):
            line = line.strip()
            # Look for lines like " 2  /path/to/soundfont.sf2"
            if line and line[0].isdigit():
                parts = line.split(None, 1)
                if parts:
                    try:
                        sf_id = int(parts[0])
                        if sf_id != 1:  # Don't unload ID 1
                            self._send_command(f"unload {sf_id}")
                            print(f"  Unloaded soundfont ID {sf_id}")
                    except ValueError:
                        pass  # Skip lines that don't start with a number
    
    def _send_command(self, command: str, timeout: float = 0.1) -> str:
        """Send command to FluidSynth and return response.
        
        Args:
            command: Command string to send
            timeout: Initial wait time in seconds before reading response
        """
        try:
            self.sock.sendall((command + "\n").encode())
            time.sleep(timeout)  # Give FluidSynth time to respond
            
            # Read all available data (may include multiple messages/errors)
            self.sock.setblocking(False)
            response_parts = []
            max_reads = 100  # Prevent infinite loop
            reads = 0
            try:
                while reads < max_reads:
                    chunk = self.sock.recv(4096).decode()
                    if not chunk:
                        break
                    response_parts.append(chunk)
                    reads += 1
                    time.sleep(0.02)  # Small delay between reads
            except BlockingIOError:
                pass  # No more data available
            finally:
                self.sock.setblocking(True)
            
            return ''.join(response_parts)
        except Exception as e:
            print(f"Error sending command to FluidSynth: {e}")
            return ""
    
    def _list_instruments(self, sf_id: int):
        """List all available instruments in the soundfont and store them."""
        inst_response = self._send_command(f"inst {sf_id}")
        
        if not inst_response or inst_response.strip() == "":
            self.available_presets = []
            return
        
        # Parse instrument list
        lines = inst_response.split('\n')
        instruments = []
        
        for line in lines:
            line = line.strip()
            # Format is: BBB-PPP Name
            # Example: "000-000 Piano"
            if line and len(line) > 8 and '-' in line[:8]:
                try:
                    bank_prog = line[:7]  # "000-000"
                    name = line[8:].strip()
                    if bank_prog[3] == '-' and bank_prog[:3].isdigit() and bank_prog[4:7].isdigit():
                        bank = int(bank_prog[:3])
                        prog = int(bank_prog[4:7])
                        instruments.append((bank, prog, name))
                except (ValueError, IndexError):
                    continue
        
        # Store available presets for cycling
        self.available_presets = instruments
        self.preset_index = 0
        
        if instruments:
            print("Available instruments:")
            print("-" * 60)
            
            # Group by bank
            current_bank = None
            for bank, prog, name in instruments:
                if bank != current_bank:
                    if current_bank is not None:
                        print()
                    print(f"Bank {bank}:")
                    current_bank = bank
                print(f"  [{prog:3d}] {name}")
            
            print("-" * 60)
            print(f"Total: {len(instruments)} instruments")
            print()
    
    def _load_soundfont(self, index: int):
        """Load a soundfont, unloading the previous one first."""
        if index < 0 or index >= len(self.soundfonts):
            return
        
        # Update index immediately so we can keep cycling on failure
        self.current_index = index
        
        # Unload OLD soundfont first to free RAM (even if new one might fail)
        if self.last_loaded_id is not None:
            unload_resp = self._send_command(f"unload {self.last_loaded_id}")
            self.last_loaded_id = None  # Clear it immediately
            self.current_sf_id = None
        
        # Load new soundfont
        sf_path = self.soundfonts[index]
        sf_name = os.path.basename(sf_path)
        print(f'\n\nLoading "{sf_name}"')
        print(f"[{index}] {sf_path}")
        # Quote the path to handle spaces in filenames
        # Use longer timeout for load command as it can take time
        response = self._send_command(f'load "{sf_path}"', timeout=1.0)
                
        # Parse the ID from response
        try:
            if "has ID" in response:
                sf_id = int(response.split("has ID")[1].strip().split()[0])
                
                # Update tracking variables
                self.current_sf_id = sf_id
                self.last_loaded_id = sf_id
                self.current_program = 0
                self.current_bank = 0
                self.preset_index = 0
                
                # List available instruments (this populates available_presets)
                self._list_instruments(sf_id)
                
                # Select first available preset if any exist
                if self.available_presets:
                    bank, prog, name = self.available_presets[0]
                    self.current_bank = bank
                    self.current_program = prog
                    select_response = self._send_command(f"select 0 {sf_id} {bank} {prog}")
                    print(f'✓ "{sf_name}" loaded as ID {sf_id}, selected Bank {bank} Program {prog}: {name}\n')
                else:
                    select_response = self._send_command(f"select 0 {sf_id} 0 0")
                    print(f'✓ "{sf_name}" loaded as ID {sf_id}, selected on channel 0\n')
            else:
                print(f"✗ Failed - no 'has ID' in response: {response.strip()}")
                print(f"   No soundfont currently loaded - press ↑/↓ to try another")
        except Exception as e:
            print(f"✗ Error parsing response: {e}")
            print(f"   Response was: {repr(response)}")
            print(f"   No soundfont currently loaded - press ↑/↓ to try another")
    
    def next_soundfont(self):
        """Load next soundfont."""
        next_index = (self.current_index + 1) % len(self.soundfonts)
        self._load_soundfont(next_index)
    
    def prev_soundfont(self):
        """Load previous soundfont."""
        prev_index = (self.current_index - 1) % len(self.soundfonts)
        self._load_soundfont(prev_index)
    
    def next_program(self):
        """Cycle to next available preset."""
        if self.current_sf_id is None:
            print("No soundfont loaded")
            return
        
        if not self.available_presets:
            print("No presets available in this soundfont")
            return
        
        # Move to next preset
        self.preset_index = (self.preset_index + 1) % len(self.available_presets)
        bank, prog, name = self.available_presets[self.preset_index]
        
        self.current_bank = bank
        self.current_program = prog
        
        self._send_command(f"select 0 {self.current_sf_id} {bank} {prog}")
        print(f"\n→ Bank {bank} Program {prog}: {name}")
    
    def prev_program(self):
        """Cycle to previous available preset."""
        if self.current_sf_id is None:
            print("No soundfont loaded")
            return
        
        if not self.available_presets:
            print("No presets available in this soundfont")
            return
        
        # Move to previous preset
        self.preset_index = (self.preset_index - 1) % len(self.available_presets)
        bank, prog, name = self.available_presets[self.preset_index]
        
        self.current_bank = bank
        self.current_program = prog
        
        self._send_command(f"select 0 {self.current_sf_id} {bank} {prog}")
        print(f"\n← Bank {bank} Program {prog}: {name}")
    
    def list_soundfonts(self):
        """List all available soundfonts."""
        print("\n" + "="*60)
        print("AVAILABLE SOUNDFONTS")
        print("="*60)
        
        for i, sf_path in enumerate(self.soundfonts):
            sf_name = os.path.basename(sf_path)
            marker = " ← CURRENT" if i == self.current_index else ""
            print(f"  [{i:2d}] {sf_name}{marker}")
        
        print("="*60)
        print(f"Total: {len(self.soundfonts)} soundfonts")
        print("Use ↑/↓ or w/s to navigate\n")
    
    def show_status(self):
        """Show current soundfont and channel status."""
        print("\n" + "="*60)
        print("CURRENT STATUS")
        print("="*60)
        
        # Show loaded soundfonts
        fonts_response = self._send_command("fonts")
        print("Loaded soundfonts:")
        print(fonts_response.strip())
        
        # Show channel assignments
        channels_response = self._send_command("channels")
        print("\nChannel assignments:")
        print(channels_response.strip())
        
        # Show our tracking info
        print("\nController tracking:")
        print(f"  current_sf_id: {self.current_sf_id}")
        print(f"  last_loaded_id: {self.last_loaded_id}")
        print(f"  current_index: {self.current_index}")
        print(f"  current_program: {self.current_program}")
        if self.current_index < len(self.soundfonts):
            print(f"  current_file: {self.soundfonts[self.current_index]}")
        print("="*60)
    
    def _get_key(self):
        """Get a single keypress (Unix/Linux)."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            # Handle arrow keys (escape sequences)
            if ch == '\x1b':
                ch += sys.stdin.read(2)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def run(self):
        """Run the controller with keyboard input."""
        self.running = True
        print("\n" + "="*60)
        print("FluidSynth Soundfont Switcher")
        print("="*60)
        print("Controls:")
        print("  ↑ / w    - Previous soundfont")
        print("  ↓ / s    - Next soundfont")
        print("  ← / a    - Previous program")
        print("  → / d    - Next program")
        print("  l        - List available soundfonts")
        print("  f        - Show status (loaded fonts, banks, programs)")
        print("  q        - Quit")
        print("="*60)
        
        try:
            while self.running:
                key = self._get_key()
                
                if key == '\x1b[A' or key == 'w':  # Up arrow or 'w'
                    self.prev_soundfont()
                elif key == '\x1b[B' or key == 's':  # Down arrow or 's'
                    self.next_soundfont()
                elif key == '\x1b[C' or key == 'd':  # Right arrow or 'd'
                    self.next_program()
                elif key == '\x1b[D' or key == 'a':  # Left arrow or 'a'
                    self.prev_program()
                elif key == 'l':  # List soundfonts
                    self.list_soundfonts()
                elif key == 'f':  # Status display
                    self.show_status()
                elif key == 'q':
                    print("\nQuitting...")
                    break
                    
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.stop()
    
    def stop(self):
        """Clean up resources."""
        self.running = False
        if self.last_loaded_id is not None:
            self._send_command(f"unload {self.last_loaded_id}")
        if hasattr(self, 'sock'):
            self.sock.close()
        print("FluidSynth controller stopped.")


def find_soundfonts(directory: str) -> List[str]:
    """
    Recursively find all .sf2 and .sf3 files in a directory.
    
    Args:
        directory: Path to directory to search
        
    Returns:
        Sorted list of absolute paths to soundfont files
    """
    soundfonts = []
    search_path = Path(directory).expanduser().resolve()
    
    if not search_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not search_path.is_dir():
        raise ValueError(f"Not a directory: {directory}")
    
    # Recursively find all .sf2 and .sf3 files
    for ext in ['*.sf2', '*.sf3']:
        soundfonts.extend(search_path.rglob(ext))
    
    # Convert to strings and sort
    soundfonts = sorted([str(sf) for sf in soundfonts])
    
    if not soundfonts:
        raise FileNotFoundError(f"No .sf2 or .sf3 files found in {directory}")
    
    return soundfonts


def main():
    """Example usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='FluidSynth Soundfont Controller')
    parser.add_argument('directory', nargs='?', 
                       default='/home/matthew.marichiba/midi-metronome/soundfonts',
                       help='Directory containing soundfonts (default: ./soundfonts)')
    parser.add_argument('--host', default='localhost',
                       help='FluidSynth server host (default: localhost)')
    parser.add_argument('--port', type=int, default=9800,
                       help='FluidSynth server port (default: 9800)')
    parser.add_argument('--channel', type=int, default=1,
                       help='MIDI channel 1-16 (default: 1)')
    
    args = parser.parse_args()
    
    # Find soundfonts in specified directory
    try:
        soundfonts = find_soundfonts(args.directory)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        print("\nUsage:")
        print(f"  {sys.argv[0]} [directory]")
        print("\nExample:")
        print(f"  {sys.argv[0]} ~/soundfonts")
        print(f"  {sys.argv[0]} /home/matthew.marichiba/midi-metronome/soundfonts/sf3")
        sys.exit(1)
    
    print("Starting FluidSynth Controller...")
    print(f"Searching in: {args.directory}")
    
    try:
        controller = FluidSynthController(
            soundfonts=soundfonts,
            fluidsynth_host=args.host,
            fluidsynth_port=args.port,
            midi_channel=args.channel
        )
        # Display available soundfonts at startup
        controller.list_soundfonts()
        controller.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
