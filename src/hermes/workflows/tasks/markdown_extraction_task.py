import os
from typing import Any, Dict, Callable

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextContainer

from ..context import WorkflowContext
from .base import Task


class MarkdownExtractionTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], printer: Callable[[str], None]):
        super().__init__(task_id, task_config, printer)

    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        input_files = context.get_global('input_files', [])
        if not input_files:
            raise ValueError(f"No input files specified for text extraction task {self.task_id}")

        extracted_texts = []
        for file_path in input_files:
            if file_path.lower().endswith('.pdf'):
                extracted_text = self.pdf_to_markdown(file_path)
                file_name = os.path.basename(file_path)
                extracted_texts.append(f"--- Content from {file_name} ---\n{extracted_text}\n")
            else:
                print(f"Warning: Skipping non-PDF file: {file_path}")

        combined_text = "\n".join(extracted_texts)
        return {
            'extracted_text': combined_text
        }

    def pdf_to_markdown(self, pdf_path):
        markdown_lines = []
        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text_content = element.get_text().strip()
                    if text_content:
                        line_parts = []
                        current_format = None
                        current_text = ""
                        for text_line in element:
                            for character in text_line:
                                if isinstance(character, LTChar):
                                    font_name = character.fontname
                                    if 'Bold' in font_name and 'Italic' in font_name:
                                        new_format = '***'
                                    elif 'Bold' in font_name:
                                        new_format = '**'
                                    elif 'Italic' in font_name:
                                        new_format = '*'
                                    else:
                                        new_format = ''
                                    if new_format != current_format:
                                        if current_text:
                                            line_parts.append(f"{current_format}{current_text}{current_format}")
                                            current_text = ""
                                        current_format = new_format
                                    current_text += character.get_text()
                        if current_text:
                            line_parts.append(f"{current_format}{current_text}{current_format}")
                        markdown_line = "".join(line_parts).strip()
                        # Convert all-caps lines to headers
                        if markdown_line.isupper():
                            markdown_line = f"# {markdown_line.capitalize()}"
                        markdown_lines.append(markdown_line)
        return "\n\n".join(markdown_lines)
