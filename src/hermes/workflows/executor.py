from typing import Dict, Any, List, Callable

from hermes.prompt_builders.base import PromptBuilder
from . import parser
from .context import WorkflowContext
from .tasks.base import Task
from ..chat_models.base import ChatModel

class WorkflowExecutor:
    def __init__(self, workflow_file: str, model: ChatModel, model_id: str, prompt_builder: PromptBuilder, input_files: List[str], initial_prompt: str, printer: Callable[[str], None]):
        self.model = model
        self.model_id = model_id
        self.printer = printer
        self.parser = parser.WorkflowParser(self.model, self.model_id, self.printer)
        self.root_task: Task = self.parser.parse(workflow_file)
        self.context = WorkflowContext()
        self.prompt_builder = prompt_builder

        # Set initial global context
        self.context.set_global('input_files', input_files)
        self.context.set_global('initial_prompt', initial_prompt)
        self.context.set_global('prompt_builder', prompt_builder)

    def execute(self) -> Dict[str, Any]:
        """Execute the workflow and return the final context."""
        self.model.initialize()

        result = self.root_task.execute(self.context)
        self.context.task_contexts[self.root_task.task_id] = result

        return result
