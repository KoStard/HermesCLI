from typing import Dict, Optional, List

from .file_system import Node
from .task_manager import TaskManager
from .task_queue import TaskStatus, Task


class TaskScheduler:
    """
    Schedules tasks for execution and maintains the mapping between nodes and tasks.
    
    This class is responsible for:
    - Registering nodes as tasks
    - Updating task statuses
    - Determining which node should be processed next
    """

    def __init__(self):
        self.task_manager = TaskManager()
        self.node_task_map: Dict[str, str] = {}  # Maps node.title -> task_id

    def register_task(self, node: Node) -> str:
        """Register a node as a task and return the task ID"""
        task_id = self.task_manager._register_task_for_node(node)
        self.node_task_map[node.title] = task_id
        return task_id

    def mark_status_of_node(self, node: Node, status: TaskStatus) -> bool:
        """Update the status of a node's associated task"""
        if node.title not in self.node_task_map:
            return False
            
        task_id = self.node_task_map[node.title]
        self.task_manager._set_task_status(task_id, status)
        return True

    def get_next_node(self) -> Optional[Node]:
        """Get the next node that should be processed"""
        # Get all pending tasks
        pending_tasks = self._get_pending_tasks()
        if not pending_tasks:
            return None

        # Get the first pending task
        next_task = pending_tasks[0]
        return self.task_manager.task_node_map.get(next_task.id)

    def initialize_root_task(self, root_node: Node = None) -> None:
        """Initialize the root task"""
        if root_node:
            self.task_manager.initialize_root_task(root_node)
        
    def request_focus_down(self, subproblem_title: str) -> bool:
        """Request to focus down to a subproblem"""
        return self.task_manager.request_focus_down(subproblem_title)
        
    def request_focus_up(self) -> bool:
        """Request to focus up to the parent problem"""
        return self.task_manager.request_focus_up()
        
    def request_fail_and_focus_up(self) -> bool:
        """Request to mark the current task as failed and focus up"""
        return self.task_manager.request_fail_and_focus_up()
        
    def get_current_node(self) -> Optional[Node]:
        """Get the node associated with the current task"""
        return self.task_manager.get_current_node()
        
    def has_current_task(self) -> bool:
        """Check if there is a current task"""
        return self.task_manager.current_task_id is not None
        
    def _get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        return self.task_manager.task_queue.get_tasks_by_status(TaskStatus.PENDING)
