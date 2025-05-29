from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.events import Event
    from hermes.chat.history import History
    from hermes.chat.interface import Interface
    from hermes.chat.messages import Message


class Participant(ABC):
    @abstractmethod
    def consume_events_and_render(self, history_snapshot: list["Message"], events: Generator["Event", None, None]):
        pass

    @abstractmethod
    def get_interface(self) -> "Interface":
        pass

    @abstractmethod
    def get_input_and_run_commands(self) -> Generator["Event", None, None]:
        pass

    @abstractmethod
    def get_author_key(self) -> str:
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def initialize_from_history(self, history: "History"):
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass
