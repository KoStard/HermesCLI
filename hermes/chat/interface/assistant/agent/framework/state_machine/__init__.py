from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode


class StateMachineNode(ABC):
    @abstractmethod
    def finish(self):
        """
        This looks from state perspective, failures and success are equal here.
        """
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        pass

    @abstractmethod
    def add_and_schedule_subnode(self, research_node: 'ResearchNode'):
        pass

    @abstractmethod
    def get_research_node(self) -> 'ResearchNode':
        pass

    @abstractmethod
    def has_pending_children(self) -> bool:
        pass

    @abstractmethod
    def get_next_child(self) -> Optional['StateMachineNode']:
        pass

    @abstractmethod
    def get_parent(self) -> Optional['StateMachineNode']:
        pass


class StateMachine(ABC):
    @abstractmethod
    def next(self) -> StateMachineNode | None:
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
