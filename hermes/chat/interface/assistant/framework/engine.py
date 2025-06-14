from abc import ABC, abstractmethod
from collections.abc import Generator

from hermes.chat.events.base import Event
from hermes.chat.interface.assistant.framework.llm_interface import LLMInterface


class AssistantEngine(ABC):
    def __init__(self, llm_interface: LLMInterface):
        self._llm_interface: LLMInterface = llm_interface

    def receive_events(self, events: Generator[Event, None, None]):
        self._consume_events(events)

    @abstractmethod
    def execute(self) -> Generator[Event, None, None]:
        pass
