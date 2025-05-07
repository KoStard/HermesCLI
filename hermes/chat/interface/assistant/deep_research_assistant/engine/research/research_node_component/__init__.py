from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode


T = TypeVar('T', bound='ResearchNodeComponent')


class ResearchNodeComponent(ABC):
    @abstractmethod
    @classmethod
    def load_for_research_node(cls: type[T], research_node: "ResearchNode") -> list[T]:
        pass

    @abstractmethod
    def save(self):
        pass
