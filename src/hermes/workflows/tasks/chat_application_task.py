from typing import Any, Dict, Callable
from .base import Task
from ..context import WorkflowContext
from ...chat_application import ChatApplication

class ChatApplicationTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], chat_application: ChatApplication, printer: Callable[[str], None]):
        super().__init__(task_id, task_config, printer)
        self.chat_application = chat_application

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        processed_files = context.get_global('processed_files', {})
        self.chat_application.set_files(processed_files)

        initial_prompt = self.get_config('initial_prompt')
        special_command = self.get_config('special_command')

        if self.print_output:
            self.printer(f"Starting chat application with {len(processed_files)} files")

        self.chat_application.run(initial_prompt, special_command)

        return {
            'status': 'completed'
        }
