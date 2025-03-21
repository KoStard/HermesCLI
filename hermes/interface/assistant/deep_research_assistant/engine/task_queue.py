import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any


class TaskStatus(Enum):
    """Status of a task in the queue"""

    PENDING = "pending"  # Task is waiting to be executed
    CREATED = "created"  # Task is created, but not yet pending
    RUNNING = "running"  # Task is currently being executed
    COMPLETED = "completed"  # Task has been completed successfully
    FAILED = "failed"  # Task has failed
    ON_HOLD = "on_hold"  # Task is on hold while child tasks are running


@dataclass
class Task:
    """
    Represents a task in the queue
    
    A task is a unit of work that needs to be completed. It has a status
    and a unique identifier.
    """
    status: TaskStatus = TaskStatus.CREATED
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    """
    Queue for managing tasks in the Deep Research system
    
    This class is responsible for:
    - Adding tasks to the queue
    - Retrieving tasks by ID or status
    - Updating task statuses
    - Removing tasks from the queue
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    def add_task(self, task: Task) -> str:
        """Add a task to the queue and return its ID"""
        self.tasks[task.id] = task
        return task.id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update the status of a task"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            return True
        return False

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with the given status"""
        return [task for task in self.tasks.values() if task.status == status]

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return list(self.tasks.values())

    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the queue"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
