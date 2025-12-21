"""Legacy line-based command UI controller."""

from ui_controller import UIController
from typing import Callable


class LegacyLineUIController(UIController):
    """
    Original text-based command interface.
    
    Accepts line-based commands:
      - start
      - stop
      - bpm <value>
      - status
      - quit
    """
    
    def run(self, on_command: Callable) -> bool:
        """Run the legacy command loop."""
        print("Commands: start, stop, bpm <value>, status, quit\n")
        
        try:
            while True:
                try:
                    cmd = input("> ").strip().lower()
                    
                    if cmd == "start":
                        on_command('start')
                    
                    elif cmd == "stop":
                        on_command('stop')
                    
                    elif cmd.startswith("bpm "):
                        try:
                            new_bpm = float(cmd[4:].strip())
                            if new_bpm < 1:
                                print("BPM must be at least 1")
                            else:
                                on_command('set_bpm', bpm=new_bpm, divisions=1)
                        except ValueError:
                            print("Invalid BPM value")
                    
                    elif cmd == "status":
                        # Note: This is display-only; we don't have a state query yet
                        # The main loop will need to handle this differently
                        on_command('status')
                    
                    elif cmd == "quit":
                        on_command('quit')
                        print("Goodbye")
                        return True
                    
                    elif cmd and cmd != "help":
                        print("Unknown command")
                
                except KeyboardInterrupt:
                    on_command('quit')
                    print("\nGoodbye")
                    return True
                except EOFError:
                    on_command('quit')
                    print("\nGoodbye")
                    return True
        
        except Exception as e:
            print(f"Error in UI loop: {e}")
            return False
