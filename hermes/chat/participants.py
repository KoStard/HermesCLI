import logging
from abc import ABC, abstractmethod
from collections.abc import Generator

from hermes.chat.event import Event
from hermes.chat.history import History
from hermes.chat.interface import Interface
from hermes.chat.interface.debug.debug_interface import DebugInterface
from hermes.chat.interface.user.interface.user_interface import UserInterface
from hermes.chat.message import Message

logger = logging.getLogger(__name__)


class Participant(ABC):
    @abstractmethod
    def consume_events(self, history_snapshot: list[Message], events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        pass

    @abstractmethod
    def act(self) -> Generator[Event, None, None]:
        pass

    @abstractmethod
    def get_author_key(self) -> str:
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def initialize_from_history(self, history: History):
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class DebugParticipant(Participant):
    interface: DebugInterface

    def __init__(self, interface: DebugInterface):
        self.interface = interface

    def consume_events(self, history_snapshot: list[Message], events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        return self.interface.render(history_snapshot, events)

    def act(self) -> Generator[Event, None, None]:
        return self.interface.get_input()

    def get_author_key(self) -> str:
        return "assistant"

    def clear(self):
        self.interface.clear()

    def initialize_from_history(self, history: History):
        self.interface.initialize_from_history(history)

    def get_name(self) -> str:
        return "assistant"


class LLMParticipant(Participant):
    def __init__(self, interface: Interface):
        self.interface = interface

    def consume_events(self, history_snapshot: list[Message], events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        logger.debug("Asked to consume events on LLM", self.interface)
        return self.interface.render(history_snapshot, events)

    def act(self) -> Generator[Event, None, None]:
        logger.debug("Asked to act on LLM", self.interface)
        return self.interface.get_input()

    def get_author_key(self) -> str:
        return "assistant"

    def clear(self):
        self.interface.clear()

    def initialize_from_history(self, history: History):
        self.interface.initialize_from_history(history)

    def get_name(self) -> str:
        return "assistant"


class UserParticipant(Participant):
    def __init__(self, interface: UserInterface):
        self.interface = interface

    def consume_events(self, history_snapshot: list[Message], events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        return self.interface.render(history_snapshot, events)

    def act(self) -> Generator[Event, None, None]:
        return self.interface.get_input()

    def get_author_key(self) -> str:
        return "user"

    def clear(self):
        self.interface.clear()

    def initialize_from_history(self, history: History):
        self.interface.initialize_from_history(history)

    def get_name(self) -> str:
        return "user"
