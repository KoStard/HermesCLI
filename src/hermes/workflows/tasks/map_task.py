from typing import Any, Dict, List, Callable
from .base import Task
from ..context import WorkflowContext

class MapTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], sub_task: Task, printer: Callable[[str], None]):
        super().__init__(task_id, task_config, printer)
        self.iterable = task_config['iterable']
        self.sub_task = sub_task

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        results = []
        iterable_value = context.get_global(self.iterable)
        output_mapping = self.sub_task.get_config('output_mapping', {})
        mapped_results = {key: [] for key in output_mapping}

        for item in iterable_value:
            sub_context = WorkflowContext()
            sub_context.global_context = context.global_context.copy()
            sub_context.set_global('item', item)
            task_result = self.sub_task.execute(sub_context)
            results.append(task_result)

            # Collect results for each output mapping
            for key, value in output_mapping.items():
                if isinstance(value, str) and value.startswith('result.'):
                    result_key = value.split('.', 1)[1]
                    if result_key in task_result:
                        mapped_results[key].append(task_result[result_key])

        # Set collected results in the global context
        for key, value in mapped_results.items():
            context.set_global(key, value)

        return {'results': results}
