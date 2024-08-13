from .base import FileProcessor
import PyPDF2
from docx import Document
import os

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
        doc = Document(file_path)
        return ' '.join(paragraph.text for paragraph in doc.paragraphs)

    def write_file(self, file_path: str, content: str, mode: str = 'w') -> None:
        with open(file_path, mode, encoding='utf-8') as file:
            file.write(content)
