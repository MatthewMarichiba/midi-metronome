"""Abstract base class for UI input controllers."""

from abc import ABC, abstractmethod
from typing import Callable


class UIController(ABC):
    """
    Abstract base for any input mechanism (keyboard, MIDI controller, OSC, etc.).
    
    Controllers are responsible for capturing user input and translating it into
    standardized commands that drive the clock's behavior.
    """
    
    @abstractmethod
    def run(self, on_command: Callable) -> bool:
        """
        Run the input loop.
        
        Call on_command(cmd_name, **kwargs) for each user action.
        The command dispatcher will route these to clock methods.
        
        Return True when user initiates quit (after on_command('quit') is called).
        
        Supported commands:
            - on_command('start')
            - on_command('stop')
            - on_command('set_bpm', bpm=<float>, divisions=<int>)
            - on_command('mute_audio')
            - on_command('unmute_audio')
            - on_command('quit')
        
        Args:
            on_command: Callable that receives command name and kwargs
        
        Returns:
            True if user quit, False on error/interrupt
        """
        pass
