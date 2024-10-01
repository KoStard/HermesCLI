from .base import FileProcessor
import PyPDF2
import docx
import os
from ..registry import register_file_processor

@register_file_processor("default")
class DefaultFileProcessor(FileProcessor):
    def read_file(self, file_path: str) -> str:
        if not self.exists(file_path):
            return "empty"
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext == '.docx':
            return self.extract_text_from_docx(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

    def extract_text_from_pdf(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return ' '.join(page.extract_text() for page in reader.pages)

    def extract_text_from_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return ' '.join(paragraph.text for paragraph in doc.paragraphs)