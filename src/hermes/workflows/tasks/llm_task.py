from typing import Any, Dict
from .base import Task
from ...chat_models.base import ChatModel
from ...workflows.context import WorkflowContext
from ...utils.file_utils import process_file_name

class LLMTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], model: ChatModel):
        super().__init__(task_id, task_config)
        self.model = model

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        prompt = self.get_config('prompt').format(**context.global_context)
        if not prompt:
            raise ValueError(f"No prompt specified for LLM task {self.task_id}")

        # Get the prompt formatter from the global context
        prompt_formatter = context.get_global('prompt_formatter')

        # Check if we should pass input files
        pass_input_files = self.get_config('pass_input_files', False)

        if pass_input_files:
            # Process input files
            input_files = context.get_global('input_files', [])
            processed_files = {}
            for file_path in input_files:
                processed_name = process_file_name(file_path)
                processed_files[processed_name] = file_path

            # Prepare the full context for the LLM with input files
            full_message = prompt_formatter.format_prompt(
                processed_files,
                prompt,
                context.get_global('initial_prompt', '')
            )
        else:
            # Prepare the full context for the LLM without input files
            full_message = prompt_formatter.format_prompt(
                {},
                prompt,
                context.get_global('initial_prompt', '')
            )

        # Send the message to the model and collect the response
        response = ""
        for chunk in self.model.send_message(full_message):
            print(chunk, end='')
            response += chunk
        print()

        return {
            'response': response,
            'prompt': prompt,
            'full_message': full_message
        }
