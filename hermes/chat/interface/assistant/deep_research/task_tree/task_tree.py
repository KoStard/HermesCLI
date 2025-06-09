from queue import Queue

from hermes.chat.interface.assistant.deep_research.research import Research, ResearchNode
from hermes.chat.interface.assistant.deep_research.research.research_node_component.problem_definition_manager import ProblemStatus
from hermes.chat.interface.assistant.deep_research.task_tree import TaskTree


class TaskTreeImpl(TaskTree):
    def __init__(self, research: Research):
        self._research = research
        self._events_queue = Queue()
        self._focused_subtree_root: ResearchNode | None = None

    def next(self) -> ResearchNode | None:
        """Should lock the thread until at least one node becomes
        ready to run or all of them finish, in which case it should return None."""
        while True:
            if node := self._find_next_available():
                return node
            _ = self._events_queue.get()
            if self._is_finished():
                return None

    def _is_finished(self) -> bool:
        """Check if all nodes in the focused subtree are in terminal states."""
        # Determine the root to check
        check_root = self._focused_subtree_root if self._focused_subtree_root else self._research.get_root_node()

        if not check_root:
            return True

        # Check all nodes in the subtree
        stack = [check_root]
        while stack:
            node = stack.pop()
            status = node.get_problem_status()
            if status not in {ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.CANCELLED}:
                return False
            stack.extend(node.list_child_nodes())
        return True

    def _find_next_available(self) -> ResearchNode | None:
        """Depth-first search for first available node that's ready to start."""
        # Determine the root to search from
        search_root = self._focused_subtree_root if self._focused_subtree_root else self._research.get_root_node()

        if not search_root:
            return None

        # Use depth-first search to find deepest available node first
        stack = [search_root]
        while stack:
            node = stack.pop()
            if node.get_problem_status() == ProblemStatus.READY_TO_START:
                return node
            # Add children in reverse order to maintain creation order
            stack.extend(reversed(node.list_child_nodes()))
        return None

    def register_node(self, node: ResearchNode):
        node.set_events_queue(self._events_queue)

    def set_focused_subtree(self, root_node: ResearchNode | None):
        """Set the focused subtree. Only nodes within this subtree will be processed."""
        self._focused_subtree_root = root_node

    def get_focused_subtree(self) -> ResearchNode | None:
        """Get the current focused subtree root node."""
        return self._focused_subtree_root
