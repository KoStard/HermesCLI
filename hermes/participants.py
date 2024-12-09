from abc import ABC, abstractmethod
import logging
from typing import Generator
from hermes_beta.history import History
from hermes_beta.interface.assistant.llm_interface import LLMInterface
from hermes_beta.interface.debug.debug_interface import DebugInterface
from hermes_beta.interface.user.user_interface import UserInterface
from hermes_beta.message import Message
from hermes_beta.event import Event

logger = logging.getLogger(__name__)

class Participant(ABC):
    @abstractmethod
    def consume_events(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
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

class DebugParticipant(Participant):
    interface: DebugInterface
    def __init__(self, interface: DebugInterface):
        self.interface = interface

    def consume_events(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        return self.interface.render(events)

    def act(self) -> Generator[Event, None, None]:
        return self.interface.get_input()
    
    def get_author_key(self) -> str:
        return "assistant"

    def clear(self):
        self.interface.clear()

    def initialize_from_history(self, history: History):
        self.interface.initialize_from_history(history)

class LLMParticipant(Participant):
    def __init__(self, interface: LLMInterface):
        self.interface = interface
    
    def consume_events(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        logger.debug("Asked to consume events on LLM", self.interface)
        return self.interface.render(events)
    
    def act(self) -> Generator[Event, None, None]:
        logger.debug("Asked to act on LLM", self.interface)
        return self.interface.get_input()

    def get_author_key(self) -> str:
        return "assistant"

    def clear(self):
        self.interface.clear()

    def initialize_from_history(self, history: History):
        self.interface.initialize_from_history(history)

class UserParticipant(Participant):
    def __init__(self, interface: UserInterface):
        self.interface = interface
    
    def consume_events(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        return self.interface.render(events)

    def act(self) -> Generator[Event, None, None]:
        return self.interface.get_input()

    def get_author_key(self) -> str:
        return "user"

    def clear(self):
        self.interface.clear()

    def initialize_from_history(self, history: History):
        self.interface.initialize_from_history(history)