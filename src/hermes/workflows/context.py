from typing import Dict, Any

class WorkflowContext:
    def __init__(self):
        self.global_context: Dict[str, Any] = {}
        self.task_contexts: Dict[str, Dict[str, Any]] = {}

    def set_global(self, key: str, value: Any):
        """Set a global context variable."""
        self.global_context[key] = value

    def get_global(self, key: str, default: Any = None) -> Any:
        """Get a global context variable."""
        return self.global_context.get(key, default)

    def set_task_context(self, task_id: str, key: str, value: Any):
        """Set a task-specific context variable."""
        if task_id not in self.task_contexts:
            self.task_contexts[task_id] = {}
        self.task_contexts[task_id][key] = value

    def get_task_context(self, task_id: str, key: str, default: Any = None) -> Any:
        """Get a task-specific context variable."""
        return self.task_contexts.get(task_id, {}).get(key, default)

    def clear_task_context(self, task_id: str):
        """Clear the context for a specific task."""
        self.task_contexts.pop(task_id, None)

    def clear_all(self):
        """Clear all context data."""
        self.global_context.clear()
        self.task_contexts.clear()
    
    def copy(self):
        """Create a copy of the current context."""
        new_context = WorkflowContext()
        new_context.global_context = self.global_context.copy()
        new_context.task_contexts = {task_id: context.copy() for task_id, context in self.task_contexts.items()}
        return new_context
