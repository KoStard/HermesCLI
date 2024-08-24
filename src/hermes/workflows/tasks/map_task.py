from typing import Any, Dict, List
from .base import Task
from ..context import WorkflowContext

class MapTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], sub_task: Task):
        super().__init__(task_id, task_config)
        self.iterable = task_config['iterable']
        self.sub_task = sub_task

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        results = []
        iterable_value = context.get_global(self.iterable)
        for item in iterable_value:
            sub_context = WorkflowContext()
            sub_context.global_context = context.global_context.copy()
            sub_context.set_global('item', item)
            task_result = self.sub_task.execute(sub_context)
            results.append(task_result)
        return {'results': results}