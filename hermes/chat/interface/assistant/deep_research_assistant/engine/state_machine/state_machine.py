from collections import deque
from typing import Optional

from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode
from hermes.chat.interface.assistant.deep_research_assistant.engine.state_machine import StateMachine, StateMachineNode


class StateMachineNodeImpl(StateMachineNode):
    def __init__(self, research_node: ResearchNode, parent: Optional['StateMachineNode'] = None):
        self._is_finished = False
        self._research_node = research_node
        self._parent = parent
        self._children_queue = deque()  # Queue of child nodes to process

    def finish(self):
        """
        This looks from state perspective, failures and success are equal here.
        """
        self._is_finished = True

    def is_finished(self) -> bool:
        return self._is_finished

    def add_and_schedule_subnode(self, research_node: 'ResearchNode'):
        """
        Add a child node to be processed next when this node is active
        """
        child_node = StateMachineNodeImpl(research_node, self)
        self._children_queue.append(child_node)

    def get_research_node(self) -> 'ResearchNode':
        """
        Get the research node associated with this state machine node
        """
        return self._research_node

    def has_pending_children(self) -> bool:
        """
        Check if this node has any pending children
        """
        return len(self._children_queue) > 0

    def get_next_child(self) -> Optional['StateMachineNode']:
        """
        Get the next child node from the queue, if any
        """
        if not self._children_queue:
            return None
        return self._children_queue.popleft()

    def get_parent(self) -> Optional['StateMachineNode']:
        """
        Get the parent node, if any
        """
        return self._parent


class StateMachineImpl(StateMachine):
    def __init__(self):
        self._root_node = None
        self._active_node = None

    def next(self) -> StateMachineNode | None:
        """
        Should automatically identify which nodes are finished and find the next one that should be picked up.
        No explicit focus_up needed.
        Returns None when all tasks finished.
        """
        # If there's no root node yet, we can't do anything
        if not self._root_node:
            return None

        # If there's no active node, start with the root
        if not self._active_node:
            self._active_node = self._root_node
            return self._active_node

        # Check if current node has pending children
        if self._active_node.has_pending_children():
            # Move to next child
            self._active_node = self._active_node.get_next_child()
            return self._active_node

        if self._active_node.is_finished():
            if self._active_node == self._root_node:
                return None

            # Otherwise, move up to parent
            parent = self._active_node.get_parent()
            self._active_node = parent
            return self._active_node

        # If we got here, something's wrong. next() has been called without finishing the task
        raise Exception("State machine next() has been called without finishing the active task")

    def set_root_research_node(self, root_research_node: 'ResearchNode'):
        """
        Set the root research node and reset the state machine
        """
        self._root_node = StateMachineNodeImpl(root_research_node)
        self._active_node = None  # Reset active node

    def reactivate_root_node(self, root_research_node: 'ResearchNode'):
        self.set_root_research_node(root_research_node)
