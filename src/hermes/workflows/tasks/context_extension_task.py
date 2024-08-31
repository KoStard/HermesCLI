import os
from typing import Any, Dict, List, Callable
from .base import Task
from ..context import WorkflowContext
from ...utils.file_utils import process_file_name

class ContextExtensionTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], printer: Callable[[str], None], workflow_dir: str):
        super().__init__(task_id, task_config, printer)
        self.files = task_config.get('files', [])
        self.workflow_dir = workflow_dir

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        existing_files = context.get_global('input_files', [])
        extended_files = existing_files + [self.resolve_path(file) for file in self.files]

        # Process file names
        processed_files = {process_file_name(file): file for file in extended_files}

        # Update the global context with the extended file list
        context.set_global('input_files', extended_files)
        context.set_global('processed_files', processed_files)

        if self.print_output:
            self.printer(f"Extended context with files: {', '.join(self.files)}")

        return {
            'extended_files': extended_files,
            'processed_files': processed_files
        }

    def resolve_path(self, file_path: str) -> str:
        if os.path.isabs(file_path):
            return file_path
        return os.path.abspath(os.path.join(self.workflow_dir, file_path))
