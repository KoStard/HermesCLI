from typing import Optional
from .base import PromptBuilder
from hermes.file_processors.base import FileProcessor

class MarkdownPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor):
        self.content = []
        self.file_processor = file_processor

    def add_text(self, text: str, name: Optional[str] = None):
        if name:
            self.content.append(f"## {name}\n\n{text}\n")
        else:
            self.content.append(f"{text}\n")

    def add_file(self, file_path: str, name: str):
        content = self.file_processor.read_file(file_path)
        self.content.append(f"## {name}\n\n```\n{content}\n```\n")

    def add_image(self, image_path: str, name: str):
        self.content.append(f"## {name}\n\n![{name}]({image_path})\n")

    def build_prompt(self) -> str:
        return "\n".join(self.content)
