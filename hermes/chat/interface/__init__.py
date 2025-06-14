"""Interface is kind of what the user sees
It has representation of the chat history
Also it has representation of the control panel
It can also show who is on the other side of the chat

Basically interface is what the user sees and interacts with
"""

import typing
from abc import ABC, abstractmethod
from collections.abc import Generator

if typing.TYPE_CHECKING:
    from hermes.chat.events.base import Event
    from hermes.chat.history import History


class Orchestrator(ABC):
    @abstractmethod
    def render(self, events: Generator["Event", None, None]):
        """Render events to the participant.
        It might yield events for the other participant.
        """

    @abstractmethod
    def get_input(self) -> Generator["Event", None, None]:
        """Get input from the participant. It propagates the input as events."""

    @abstractmethod
    def clear(self):
        pass

    def initialize_from_history(self, history: "History"):  # noqa: B027
        pass

    @abstractmethod
    def prepare(self):
        pass
