from queue import Queue

from hermes.chat.interface.assistant.agent_old.framework.research import Research, ResearchNode
from hermes.chat.interface.assistant.agent_old.framework.research.research_node_component.problem_definition_manager import ProblemStatus
from hermes.chat.interface.assistant.agent_old.framework.task_tree import TaskTree


class TaskTreeImpl(TaskTree):
    def __init__(self, research: Research):
        self._research = research
        self._events_queue = Queue()

    def next(self) -> ResearchNode | None:
        """
        Should lock the thread until at least one node becomes ready to run or all of them finish, in which case it should return None.
        """
        while True:
            if node := self._find_next_available():
                return node
            _ = self._events_queue.get()
            if self._is_finished():
                return None

    def _is_finished(self) -> bool:
        """Check if all nodes are in terminal states."""
        root = self._research.get_root_node()
        if not root:
            return True

        # Check all nodes in the tree
        stack = [root]
        while stack:
            node = stack.pop()
            status = node.get_problem_status()
            if status not in {ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.CANCELLED}:
                return False
            stack.extend(node.list_child_nodes())
        return True

    def _find_next_available(self) -> ResearchNode | None:
        """Depth-first search for first available node that's ready to start."""
        root = self._research.get_root_node()
        if not root:
            return None

        # Use depth-first search to find deepest available node first
        stack = [root]
        while stack:
            node = stack.pop()
            if node.get_problem_status() == ProblemStatus.READY_TO_START:
                return node
            # Add children in reverse order to maintain creation order
            stack.extend(reversed(node.list_child_nodes()))
        return None

    def register_node(self, node: ResearchNode):
        node.set_events_queue(self._events_queue)
