from typing import Dict, Any, List
from .parser import WorkflowParser
from .context import WorkflowContext
from .tasks.base import Task
from .tasks.llm_task import LLMTask
from .tasks.shell_task import ShellTask
from ..chat_models.base import ChatModel

class WorkflowExecutor:
    def __init__(self, workflow_file: str, model: ChatModel):
        self.parser = WorkflowParser()
        self.context = WorkflowContext()
        self.model = model
        self.workflow = self.parser.parse(workflow_file)
        self.tasks: List[Task] = []

    def prepare_tasks(self):
        """Prepare the list of tasks based on the parsed workflow."""
        for task_id, task_config in self.workflow.get('tasks', {}).items():
            task_type = task_config.get('type')
            if task_type == 'llm':
                self.tasks.append(LLMTask(task_id, task_config, self.model))
            elif task_type == 'shell':
                self.tasks.append(ShellTask(task_id, task_config))
            else:
                raise ValueError(f"Unknown task type: {task_type}")

    def execute(self) -> Dict[str, Any]:
        """Execute the workflow and return the final context."""
        self.prepare_tasks()
        
        for task in self.tasks:
            print(f"Executing task: {task.task_id}")
            result = task.execute(self.context.global_context)
            self.context.set_task_context(task.task_id, 'result', result)
            
            # Update global context with task result
            self.context.set_global(f"{task.task_id}_result", result)
            
            # Check for output mapping
            output_mapping = task.get_config('output_mapping', {})
            for key, value in output_mapping.items():
                if isinstance(value, str) and value.startswith('result.'):
                    result_key = value.split('.', 1)[1]
                    if result_key in result:
                        self.context.set_global(key, result[result_key])
        
        return self.context.global_context
