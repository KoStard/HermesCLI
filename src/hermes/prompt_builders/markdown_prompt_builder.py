from typing import Optional
from .base import PromptBuilder
from hermes.file_processors.base import FileProcessor
from ..decorators import register_prompt_builder

@register_prompt_builder("markdown")
class MarkdownPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor):
        self.content = []
        self.file_processor = file_processor

    def add_text(self, text: str, name: Optional[str] = None):
        if name:
            self.content.append(f"## {name}\n\n{text}")
        else:
            self.content.append(f"{text}")

    def add_file(self, file_path: str, name: str):
        content = self.file_processor.read_file(file_path)
        self.content.append(f"## {name}\n\n```\n{content}\n```")

    def add_image(self, image_path: str, name: str):
        raise NotImplementedError("Images are not supported in Markdown format")

    def build_prompt(self) -> str:
        return "\n".join(self.content)

    def erase(self):
        self.content = []
