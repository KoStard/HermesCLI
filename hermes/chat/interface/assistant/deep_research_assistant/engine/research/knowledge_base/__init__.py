from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.research import Research


class KnowledgeBase(ABC):
    @abstractmethod
    def load_for_research(self, research: "Research") -> "KnowledgeBase":
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def add_content(self, content: str):
        pass
