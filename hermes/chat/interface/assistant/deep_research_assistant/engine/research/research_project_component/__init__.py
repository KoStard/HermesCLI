from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.research import Research

T = TypeVar('T', bound='ResearchComponent')

class ResearchComponent(ABC):
    @abstractmethod
    @classmethod
    def load_for_research(cls: type[T], research: "Research") -> list[T]:
        pass

    @abstractmethod
    def save(self):
        pass
