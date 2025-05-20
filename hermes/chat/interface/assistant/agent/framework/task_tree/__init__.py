from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode


class TaskTree(ABC):
    @abstractmethod
    def next(self) -> "ResearchNode | None":
        """
        Should automatically identify which nodes are finished and find the next one that should be picked up.
        No explicit focus_up needed.
        Returns None when all tasks finished.
        """
        pass

    @abstractmethod
    def register_node(self, node: "ResearchNode"):
        pass
