from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode


class Task:
    pass


class TaskTree(ABC):
    @abstractmethod
    def next(self) -> "ResearchNode | None":
        """Should automatically identify which nodes are finished and find the next one that should be picked up.
        No explicit focus_up needed.
        Returns None when all tasks finished.
        """

    @abstractmethod
    def register_node(self, node: "ResearchNode"):
        pass

    @abstractmethod
    def set_focused_subtree(self, root_node: "ResearchNode | None"):
        """Set the focused subtree. Only nodes within this subtree will be processed.
        Pass None to clear the focus and process the entire tree.
        """

    @abstractmethod
    def get_focused_subtree(self) -> "ResearchNode | None":
        """Get the current focused subtree root node."""
