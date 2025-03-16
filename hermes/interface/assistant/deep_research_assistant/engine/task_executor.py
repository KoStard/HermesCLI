import threading
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

from .file_system import FileSystem, Node
from .task_queue import Task, TaskQueue, TaskStatus


class TaskExecutorStatus(Enum):
    """Status of the task executor"""
    IDLE = "idle"
    RUNNING = "running"
    SHUTDOWN = "shutdown"


class TaskExecutor:
    """
    Manages the execution of tasks in the Deep Research system.
    
    This executor handles focus changes between problems and subproblems,
    ensuring that parent tasks don't complete until all child tasks are done.
    """
    
    def __init__(self, file_system: FileSystem):
        self.file_system = file_system
        self.task_queue = TaskQueue()
        self.status = TaskExecutorStatus.IDLE
        self.current_task_id: Optional[str] = None
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.task_relationships: Dict[str, Set[str]] = {}  # parent_id -> set of child_ids
        self.task_node_map: Dict[str, Node] = {}  # task_id -> Node
        
        # Start with root task if available
        if self.file_system.root_node:
            self._initialize_root_task()
    
    def _initialize_root_task(self) -> None:
        """Initialize the root task"""
        with self.lock:
            root_task = Task(
                node=self.file_system.root_node,
                status=TaskStatus.PENDING
            )
            task_id = self.task_queue.add_task(root_task)
            self.task_node_map[task_id] = self.file_system.root_node
            self._start_next_task()
    
    def request_focus_down(self, subproblem_title: str) -> bool:
        """
        Request to focus down to a subproblem
        
        Args:
            subproblem_title: Title of the subproblem to focus on
            
        Returns:
            bool: True if the request was accepted, False otherwise
        """
        with self.lock:
            if not self.current_task_id:
                return False
                
            current_task = self.task_queue.get_task(self.current_task_id)
            if not current_task:
                return False
                
            current_node = current_task.node
            if subproblem_title not in current_node.subproblems:
                return False
                
            # Get the subproblem node
            subproblem_node = current_node.subproblems[subproblem_title]
            
            # Create a new task for the subproblem
            subproblem_task = Task(
                node=subproblem_node,
                status=TaskStatus.PENDING,
                parent_task_id=self.current_task_id
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
            self.task_queue.update_task_status(self.current_task_id, TaskStatus.ON_HOLD)
            
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
        with self.lock:
            if not self.current_task_id:
                return False
                
            current_task = self.task_queue.get_task(self.current_task_id)
            if not current_task:
                return False
                
            # If this is the root task, mark it as completed and we're done
            if not current_task.parent_task_id:
                self.task_queue.update_task_status(self.current_task_id, TaskStatus.COMPLETED)
                self.current_task_id = None
                return True
                
            # Check if all sibling tasks are completed
            parent_task_id = current_task.parent_task_id
            if parent_task_id in self.task_relationships:
                child_task_ids = self.task_relationships[parent_task_id]
                
                # Mark this task as completed
                self.task_queue.update_task_status(self.current_task_id, TaskStatus.COMPLETED)
                
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
                    self.task_queue.update_task_status(parent_task_id, TaskStatus.PENDING)
                    
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
            self.task_queue.update_task_status(self.current_task_id, TaskStatus.COMPLETED)
            self.current_task_id = None
            self._start_next_task()
            return True
    
    def request_fail_and_focus_up(self) -> bool:
        """
        Request to mark the current task as failed and focus up
        
        Returns:
            bool: True if the request was accepted, False otherwise
        """
        with self.lock:
            if not self.current_task_id:
                return False
                
            current_task = self.task_queue.get_task(self.current_task_id)
            if not current_task:
                return False
                
            # Mark this task as failed
            self.task_queue.update_task_status(self.current_task_id, TaskStatus.FAILED)
            
            # If this is the root task, we're done
            if not current_task.parent_task_id:
                self.current_task_id = None
                return True
                
            # Get the parent task
            parent_task_id = current_task.parent_task_id
            
            # Mark the parent task as pending so it can be picked up
            self.task_queue.update_task_status(parent_task_id, TaskStatus.PENDING)
            
            # Clear the current task
            self.current_task_id = None
            
            # Start the next task (which should be the parent task)
            self._start_next_task()
            
            return True
    
    def _start_next_task(self) -> None:
        """Start the next pending task"""
        with self.lock:
            # If we already have a running task, don't start another one
            if self.current_task_id:
                return
                
            # Get all pending tasks
            pending_tasks = self.task_queue.get_tasks_by_status(TaskStatus.PENDING)
            if not pending_tasks:
                return
                
            # Start the first pending task
            # In a more complex system, we might prioritize tasks differently
            next_task = pending_tasks[0]
            self.task_queue.update_task_status(next_task.id, TaskStatus.RUNNING)
            self.current_task_id = next_task.id
    
    def get_current_node(self) -> Optional[Node]:
        """Get the node associated with the current task"""
        with self.lock:
            if not self.current_task_id:
                return None
                
            current_task = self.task_queue.get_task(self.current_task_id)
            if not current_task:
                return None
                
            return current_task.node
    
    def shutdown(self) -> None:
        """Shutdown the task executor"""
        with self.lock:
            self.status = TaskExecutorStatus.SHUTDOWN
