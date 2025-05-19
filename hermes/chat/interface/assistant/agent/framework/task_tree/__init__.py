from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode


class TaskTreeNodeExecutionStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    PENDING_CHILDREN = "PENDING_CHILDREN"
    FINISHED = "FINISHED"

class TaskTreeNode(ABC):
    @abstractmethod
    def finish(self):
        """
        This looks from state perspective, failures and success are equal here.
        """
        pass

    @abstractmethod
    def mark_as_running(self):
        pass

    @abstractmethod
    def wait_for_children(self, children: list['TaskTreeNode']):
        pass

    @abstractmethod
    def refresh_pending_children(self):
        pass

    @abstractmethod
    def get_status(self) -> TaskTreeNodeExecutionStatus:
        pass

    @abstractmethod
    def add_subtask(self, research_node: 'ResearchNode'):
        pass

    @abstractmethod
    def get_research_node(self) -> 'ResearchNode':
        pass

    @abstractmethod
    def get_parent(self) -> Optional['TaskTreeNode']:
        pass


class TaskTree(ABC):
    @abstractmethod
    def next(self) -> TaskTreeNode | None:
        """
        Should automatically identify which nodes are finished and find the next one that should be picked up.
        No explicit focus_up needed.
        Returns None when all tasks finished.
        """
        pass

    @abstractmethod
    def set_root_research_node(self, root_research_node: 'ResearchNode'):
        pass

    @abstractmethod
    def reactivate_root_node(self, root_research_node: 'ResearchNode'):
        pass
