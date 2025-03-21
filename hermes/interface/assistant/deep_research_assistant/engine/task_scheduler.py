from enum import Enum
from typing import Dict, Optional, Set

from .file_system import Node
from .task_queue import Task, TaskQueue, TaskStatus

class TaskScheduler:
    """
    What should the API of task scheduled be?
    - register node
    - mark status of node
    - get_next_node
    """

    def __init__(self):
        self.task_queue = TaskQueue()
        self.task_node_map: Dict[str, Node] = {}  # task_id -> Node
        self.node_task_map: Dict[str, Task] = {}

    def register_task(self, node: Node):
        task = Task()
        self.task_node_map[task.id] = node
        self.node_task_map[node.title] = task
        self.task_queue.add_task(task)

    def mark_status_of_node(self, node: Node, status: TaskStatus) -> bool:
        task = self.node_task_map[node.title]
        return self.task_queue.update_task_status(task.id, status)

    def get_next_node(self) -> Optional[Node]:
        if self.task_queue.get_tasks_by_status(TaskStatus.RUNNING):
            raise Exception("Tasks are still running")

        pending_tasks = self.task_queue.get_tasks_by_status(TaskStatus.PENDING)
        if not pending_tasks:
            return None

        task = pending_tasks[0]
        return self.task_node_map[task.id]

    # From here goes the old implementation, we should move all this logic somewhere else or get dir of them


    """
    Manages the execution of tasks in the Deep Research system.

    This executor handles focus changes between problems and subproblems,
    ensuring that parent tasks don't complete until all child tasks are done.
    """

    def initialize_root_task(self, root_node: Node) -> None:
        """Initialize the root task"""
        task_id = self._register_task_for_node(root_node)
        self._set_task_status(task_id, TaskStatus.PENDING)
        self._start_next_task()

    def request_focus_down(self, subproblem_title: str) -> bool:
        """
        Request to focus down to a subproblem

        Args:
            subproblem_title: Title of the subproblem to focus on

        Returns:
            bool: True if the request was accepted, False otherwise
        """
        if not self.current_task_id:
            return False

        current_node = self.task_node_map[self.current_task_id]

        if subproblem_title not in current_node.subproblems:
            return False

        # Get the subproblem node
        subproblem_node = current_node.subproblems[subproblem_title]

        # Create a new task for the subproblem
        subproblem_task = Task(
            status=TaskStatus.PENDING,
            parent_task_id=self.current_task_id,
        )

        # Add the task to the queue
        subproblem_task_id = self.task_queue.add_task(subproblem_task)

        # Update task relationships
        if self.current_task_id not in self.task_relationships:
            self.task_relationships[self.current_task_id] = set()
        self.task_relationships[self.current_task_id].add(subproblem_task_id)

        # Map the task ID to the node
        self.task_node_map[subproblem_task_id] = subproblem_node

        # Mark the current task as on hold
        self._set_task_status(self.current_task_id, TaskStatus.ON_HOLD)

        # Start the next task (which should be the subproblem task)
        self.current_task_id = None
        self._start_next_task()

        return True

    def request_focus_up(self) -> bool:
        """
        Request to focus up to the parent problem

        Returns:
            bool: True if the request was accepted, False otherwise
        """
        if not self.current_task_id:
            return False

        current_task = self.task_queue.get_task(self.current_task_id)
        if not current_task:
            return False

        # If this is the root task, mark it as completed and we're done
        if not current_task.parent_task_id:
            self._set_task_status(
                self.current_task_id, TaskStatus.COMPLETED
            )
            self.current_task_id = None
            return True

        # Check if all sibling tasks are completed
        parent_task_id = current_task.parent_task_id
        if parent_task_id in self.task_relationships:
            child_task_ids = self.task_relationships[parent_task_id]

            # Mark this task as completed
            self._set_task_status(
                self.current_task_id, TaskStatus.COMPLETED
            )

            # Check if all sibling tasks are completed
            all_siblings_completed = True
            for child_id in child_task_ids:
                if child_id == self.current_task_id:
                    continue

                child_task = self.task_queue.get_task(child_id)
                if child_task and child_task.status != TaskStatus.COMPLETED:
                    all_siblings_completed = False
                    break

            # If all siblings are completed, we can focus up
            if all_siblings_completed:
                # Mark the parent task as pending so it can be picked up
                self._set_task_status(
                    parent_task_id, TaskStatus.PENDING
                )

                # Clear the current task
                self.current_task_id = None

                # Start the next task (which should be the parent task)
                self._start_next_task()

                return True
            else:
                # Some siblings are still running or pending
                # We've already marked this task as completed
                # Start the next task (which should be a sibling)
                self.current_task_id = None
                self._start_next_task()
                return False

        # No parent-child relationship found, just mark as completed and move on
        self._set_task_status(
            self.current_task_id, TaskStatus.COMPLETED
        )
        self.current_task_id = None
        self._start_next_task()
        return True

    def request_fail_and_focus_up(self) -> bool:
        """
        Request to mark the current task as failed and focus up

        Returns:
            bool: True if the request was accepted, False otherwise
        """
        if not self.current_task_id:
            return False

        current_task = self.task_queue.get_task(self.current_task_id)
        if not current_task:
            return False

        # Mark this task as failed
        self._set_task_status(self.current_task_id, TaskStatus.FAILED)

        # If this is the root task, we're done
        if not current_task.parent_task_id:
            self.current_task_id = None
            return True

        # Get the parent task
        parent_task_id = current_task.parent_task_id

        # Mark the parent task as pending so it can be picked up
        self._set_task_status(parent_task_id, TaskStatus.PENDING)

        # Clear the current task
        self.current_task_id = None

        # Start the next task (which should be the parent task)
        self._start_next_task()

        return True

    def _register_task_for_node(self, node: Node):
        """Register a task for a node"""
        task = Task()
        task_id = self.task_queue.add_task(task)
        self.task_node_map[task_id] = node
        return task_id

    def _set_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Set the status of a task"""
        self.task_queue.update_task_status(task_id, status)

    def _start_next_task(self) -> None:
        """Start the next pending task"""
        # If we already have a running task, don't start another one
        if self.current_task_id:
            raise Exception("Already have a running task")

        # Get all pending tasks
        pending_tasks = self.task_queue.get_tasks_by_status(TaskStatus.PENDING)
        if not pending_tasks:
            return

        # Start the first pending task
        # In a more complex system, we might prioritize tasks differently
        next_task = pending_tasks[0]
        self._set_task_status(next_task.id, TaskStatus.RUNNING)
        self.current_task_id = next_task.id

    def get_current_node(self) -> Optional[Node]:
        """Get the node associated with the current task"""
        if not self.current_task_id:
            return None

        return self.task_node_map[self.current_task_id]
