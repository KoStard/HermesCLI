from queue import Queue

from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode
from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTree


class TaskTreeImpl(TaskTree):
    def __init__(self, research: Research):
        self._research = research
        self._events_queue = Queue()

    def next(self) -> ResearchNode | None:
        """
        Should lock the thread until at least one node becomes ready to run or all of them finish, in which case it should return None.
        """
        while True:
            _ = self._events_queue.get()
            if self._is_finished():
                return None
            if node := self._find_next_available():
                return node

    def _is_finished(self) -> bool:
        # All are finished or failed or cancelled
        pass

    def _find_next_available(self) -> ResearchNode | None:
        # At least one that is ready to be picked up
        pass

    def register_node(self, node: ResearchNode):
        node.set_events_queue(self._events_queue)
