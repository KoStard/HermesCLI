from typing import Any, Dict, Optional, Callable
from .base import Task
from ..context import WorkflowContext

class IfElseTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], if_task: Task, printer: Callable[[str], None], else_task: Optional[Task] = None):
        super().__init__(task_id, task_config, printer)
        self.condition = task_config['condition']
        self.if_task = if_task
        self.else_task = else_task

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        condition_result = eval(self.condition, {}, context.global_context)
        if condition_result:
            return self.if_task.execute(context)
        elif self.else_task:
            return self.else_task.execute(context)
        else:
            return {}