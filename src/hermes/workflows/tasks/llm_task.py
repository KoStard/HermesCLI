from typing import Any, Dict, Callable
from .base import Task
from ...chat_models.base import ChatModel
from ...workflows.context import WorkflowContext
from ...utils.file_utils import process_file_name
from ...prompt_builders.base import PromptBuilder

class LLMTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], model: ChatModel, printer: Callable[[str], None]):
        super().__init__(task_id, task_config, printer)
        self.model = model

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        prompt = self.get_config('prompt').format(**context.global_context)
        if not prompt:
            raise ValueError(f"No prompt specified for LLM task {self.task_id}")

        # Get the prompt builder from the global context
        prompt_builder: PromptBuilder = context.get_global('prompt_builder')

        # Check if we should pass input files
        pass_input_files = self.get_config('pass_input_files', False)

        if pass_input_files:
            # Process input files
            input_files = context.get_global('input_files', [])
            for file_path in input_files:
                processed_name = process_file_name(file_path)
                prompt_builder.add_file(file_path, processed_name)

        # Add the prompt text
        prompt_builder.add_text(prompt, "Task Prompt")

        # Add initial prompt if it exists
        initial_prompt = context.get_global('initial_prompt', '')
        if initial_prompt:
            prompt_builder.add_text(initial_prompt, "Initial Prompt")

        # Build the full message
        full_message = prompt_builder.build_prompt()

        # Send the message to the model and collect the response
        response = ""
        for chunk in self.model.send_message(full_message):
            if self.print_output:
                self.printer(chunk, end='')
            response += chunk
        if self.print_output:
            self.printer("\n")

        return {
            'response': response,
            'prompt': prompt,
            'full_message': full_message
        }
