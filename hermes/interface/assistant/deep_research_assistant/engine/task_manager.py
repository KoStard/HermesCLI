from typing import Dict, Optional, Set, List

from .file_system import Node
from .task_queue import Task, TaskQueue, TaskStatus


class TaskManager:
    """
    Manages the execution flow between tasks, handling focus changes between problems and subproblems.
    
    This class is responsible for:
    - Managing parent-child relationships between tasks
    - Handling focus changes (up/down) between problems
    - Tracking the current active task
    """

    def __init__(self):
        self.task_queue = TaskQueue()
        self.task_node_map: Dict[str, Node] = {}  # Maps task_id -> Node
        self.current_task_id: Optional[str] = None
        self.task_relationships: Dict[str, Set[str]] = {}  # parent_task_id -> set of child_task_ids

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
        subproblem_task = Task()
        subproblem_task.status = TaskStatus.PENDING

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

        # Mark this task as completed
        self._set_task_status(self.current_task_id, TaskStatus.COMPLETED)
        
        # Find the parent task by checking relationships
        parent_task_id = self._find_parent_task_id(self.current_task_id)
        
        # If no parent found, we're at the root task
        if not parent_task_id:
            self.current_task_id = None
            return True

        # Check if all sibling tasks are completed
        if parent_task_id in self.task_relationships:
            child_task_ids = self.task_relationships[parent_task_id]

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
                self._set_task_status(parent_task_id, TaskStatus.PENDING)

        # Clear the current task
        self.current_task_id = None

        # Start the next task (which should be the parent task if all siblings completed)
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

        # Mark this task as failed
        self._set_task_status(self.current_task_id, TaskStatus.FAILED)
        
        # Find the parent task
        parent_task_id = self._find_parent_task_id(self.current_task_id)
        
        # If this is the root task, we're done
        if not parent_task_id:
            self.current_task_id = None
            return True

        # Mark the parent task as pending so it can be picked up
        self._set_task_status(parent_task_id, TaskStatus.PENDING)

        # Clear the current task
        self.current_task_id = None

        # Start the next task (which should be the parent task)
        self._start_next_task()

        return True

    def _find_parent_task_id(self, task_id: str) -> Optional[str]:
        """Find the parent task ID for a given task ID"""
        for parent_id, children in self.task_relationships.items():
            if task_id in children:
                return parent_id
        return None

    def _register_task_for_node(self, node: Node) -> str:
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
            return

        # Get all pending tasks
        pending_tasks = self.task_queue.get_tasks_by_status(TaskStatus.PENDING)
        if not pending_tasks:
            return

        # Start the first pending task
        next_task = pending_tasks[0]
        self._set_task_status(next_task.id, TaskStatus.RUNNING)
        self.current_task_id = next_task.id

    def get_current_node(self) -> Optional[Node]:
        """Get the node associated with the current task"""
        if not self.current_task_id:
            return None

        return self.task_node_map.get(self.current_task_id)
    
    def get_task_status_summary(self) -> Dict:
        """Get a summary of task statuses"""
        summary = {status: 0 for status in TaskStatus}
        
        for task in self.task_queue.get_all_tasks():
            summary[task.status] += 1
            
        return summary
    
    def get_child_tasks_summary(self, task_id: str) -> Dict:
        """Get a summary of child task statuses for a given task"""
        if task_id not in self.task_relationships:
            return {}
            
        summary = {status: 0 for status in TaskStatus}
        
        for child_id in self.task_relationships[task_id]:
            child_task = self.task_queue.get_task(child_id)
            if child_task:
                summary[child_task.status] += 1
                
        return summary
