from typing import Any, Dict
from .base import Task
from ...chat_models.base import ChatModel
from ...workflows.context import WorkflowContext

class LLMTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], model: ChatModel):
        super().__init__(task_id, task_config)
        self.model = model

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        prompt = self.get_config('prompt')
        if not prompt:
            raise ValueError(f"No prompt specified for LLM task {self.task_id}")

        # Get the prompt formatter and file processor from the global context
        prompt_formatter = context.get_global('prompt_formatter')
        file_processor = context.get_global('file_processor')

        # Format the prompt using the prompt formatter
        formatted_prompt = prompt_formatter.format(prompt, context.global_context)

        # Process input files
        input_files = context.get_global('input_files', [])
        processed_files = {}
        for file_path in input_files:
            processed_files[file_path] = file_processor.read_file(file_path)

        # Prepare the full context for the LLM
        full_context = prompt_formatter.build_context(
            formatted_prompt,
            processed_files,
            context.get_global('initial_prompt', '')
        )

        # Send the message to the model and collect the response
        response = ""
        for chunk in self.model.send_message(full_context):
            response += chunk

        return {
            'response': response,
            'prompt': formatted_prompt,
            'full_context': full_context,
            'processed_files': processed_files
        }
