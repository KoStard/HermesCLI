import uuid
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from hermes.interface.assistant.deep_research_assistant.engine.file_system import Node


class TaskStatus(Enum):
    """Status of a task in the queue"""
    PENDING = "pending"  # Task is waiting to be executed
    RUNNING = "running"  # Task is currently being executed
    COMPLETED = "completed"  # Task has been completed successfully
    FAILED = "failed"  # Task has failed
    ON_HOLD = "on_hold"  # Task is on hold while child tasks are running


@dataclass
class Task:
    """Represents a task in the queue"""
    node: Node
    status: TaskStatus
    parent_task_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class TaskQueue:
    """Queue for managing tasks in the Deep Research system"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        
    def add_task(self, task: Task) -> str:
        """Add a task to the queue and return its ID"""
        with self.lock:
            task.updated_at = time.time()
            self.tasks[task.id] = task
            return task.id
            
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        with self.lock:
            return self.tasks.get(task_id)
            
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update the status of a task"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = status
                self.tasks[task_id].updated_at = time.time()
                return True
            return False
            
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with the given status"""
        with self.lock:
            return [task for task in self.tasks.values() if task.status == status]
            
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        with self.lock:
            return list(self.tasks.values())
            
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the queue"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                return True
            return False
    
    def get_child_tasks(self, parent_task_id: str) -> List[Task]:
        """Get all child tasks for a given parent task"""
        with self.lock:
            return [task for task in self.tasks.values() if task.parent_task_id == parent_task_id]
    
    def are_all_child_tasks_completed(self, parent_task_id: str) -> bool:
        """Check if all child tasks for a given parent task are completed"""
        with self.lock:
            child_tasks = self.get_child_tasks(parent_task_id)
            if not child_tasks:
                return True
            
            return all(task.status == TaskStatus.COMPLETED or task.status == TaskStatus.FAILED 
                      for task in child_tasks)
