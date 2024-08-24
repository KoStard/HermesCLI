import os
from typing import Any, Dict, List
from PyPDF2 import PdfReader
from .base import Task
from ...workflows.context import WorkflowContext

class TextExtractionTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any]):
        super().__init__(task_id, task_config)

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        input_files = context.get_global('input_files', [])
        if not input_files:
            raise ValueError(f"No input files specified for text extraction task {self.task_id}")

        extracted_texts = []
        for file_path in input_files:
            if file_path.lower().endswith('.pdf'):
                extracted_text = self.extract_text_from_pdf(file_path)
                file_name = os.path.basename(file_path)
                extracted_texts.append(f"--- Content from {file_name} ---\n{extracted_text}\n")
            else:
                print(f"Warning: Skipping non-PDF file: {file_path}")

        combined_text = "\n".join(extracted_texts)
        return {
            'extracted_text': combined_text
        }

    def extract_text_from_pdf(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
