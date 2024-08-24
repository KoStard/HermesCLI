from typing import Any, Dict
from .base import Task
from ...chat_models.base import ChatModel

class LLMTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], model: ChatModel):
        super().__init__(task_id, task_config)
        self.model = model

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.get_config('prompt')
        if not prompt:
            raise ValueError(f"No prompt specified for LLM task {self.task_id}")

        # Format the prompt with the current context
        try:
            formatted_prompt = prompt.format(**context)
        except KeyError as e:
            raise ValueError(f"Error formatting prompt for task {self.task_id}: {e}")

        # Prepare the full context for the LLM
        full_context = f"Input files: {context.get('input_files', [])}\n"
        full_context += f"Initial prompt: {context.get('initial_prompt', '')}\n\n"
        full_context += formatted_prompt

        # Send the message to the model and collect the response
        response = ""
        for chunk in self.model.send_message(full_context):
            response += chunk

        return {
            'response': response,
            'prompt': formatted_prompt,
            'full_context': full_context
        }
