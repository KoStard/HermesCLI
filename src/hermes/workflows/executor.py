from typing import Dict, Any, List
from .parser import WorkflowParser
from .context import WorkflowContext
from .tasks.base import Task
from ..chat_models.base import ChatModel
from ..prompt_formatters.base import PromptFormatter

class WorkflowExecutor:
    def __init__(self, workflow_file: str, model: ChatModel, prompt_formatter: PromptFormatter, input_files: List[str], initial_prompt: str):
        self.model = model
        self.parser = WorkflowParser(self.model)
        self.context = WorkflowContext()
        self.prompt_formatter = prompt_formatter
        self.workflow = self.parser.parse(workflow_file)
        self.tasks: Dict[str, Task] = self.workflow.get('tasks', {})

        # Set initial global context
        self.context.set_global('input_files', input_files)
        self.context.set_global('initial_prompt', initial_prompt)
        self.context.set_global('prompt_formatter', prompt_formatter)

    def execute(self) -> Dict[str, Any]:
        """Execute the workflow and return the final context."""
        self.model.initialize()

        for task_id, task in self.tasks.items():
            print(f"Executing task: {task_id}")
            result = task.execute(self.context)

            # Check for output mapping
            output_mapping = task.get_config('output_mapping', {})
            for key, value in output_mapping.items():
                if isinstance(value, str) and value.startswith('result.'):
                    result_key = value.split('.', 1)[1]
                    if result_key in result:
                        self.context.set_global(key, result[result_key])

        return self.context.global_context
