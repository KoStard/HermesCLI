from typing import Any, Dict
from .base import Task
from ...workflows.context import WorkflowContext
from ...file_processors.default import DefaultFileProcessor

class TextExtractionTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any]):
        super().__init__(task_id, task_config)
        self.file_processor = DefaultFileProcessor()

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        file_path = self.get_config('file_path')
        if not file_path:
            raise ValueError(f"No file path specified for text extraction task {self.task_id}")

        # Use the file path from the config, or try to get it from the context
        file_path = file_path.format(**context.global_context)

        extracted_text = self.file_processor.read_file(file_path)

        return {
            'extracted_text': extracted_text,
            'file_path': file_path
        }
