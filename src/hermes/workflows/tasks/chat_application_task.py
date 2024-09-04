from typing import Any, Dict, Callable

from hermes.context_providers.file_context_provider import FileContextProvider
from .base import Task
from ..context import WorkflowContext
from ...chat_application import ChatApplication

class ChatApplicationTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], chat_application: ChatApplication, printer: Callable[[str], None]):
        super().__init__(task_id, task_config, printer)
        self.chat_application = chat_application

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        input_files = context.get_global('input_files', {})
        file_context_provider = FileContextProvider()
        file_context_provider.files = input_files
        self.chat_application.context_orchestrator.context_providers = [file_context_provider]

        initial_prompt = self.get_config('initial_prompt')
        special_command = self.get_config('special_command')

        if self.print_output:
            self.printer(f"Starting chat application with {len(input_files)} files")

        self.chat_application.run(initial_prompt, special_command)

        return {
            'status': 'completed'
        }
