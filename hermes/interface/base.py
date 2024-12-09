"""
Interface is kind of what the user sees
It has representation of the chat history
Also it has representation of the control panel
It can also show who is on the other side of the chat

Basically interface is what the user sees and interacts with
"""

from abc import ABC, abstractmethod
from typing import Generator
from hermes_beta.event import Event
from hermes_beta.history import History

class Interface(ABC):
    @abstractmethod
    def render(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        """
        Render events to the participant.
        It might yield events for the other participant.
        """
        pass

    @abstractmethod
    def get_input(self) -> Generator[Event, None, None]:
        """
        Get input from the participant. It propagates the input as events.
        """
        pass

    @abstractmethod
    def clear(self):
        pass

    def initialize_from_history(self, history: History):
        pass