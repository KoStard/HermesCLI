import xml.etree.ElementTree as ET
from typing import Optional
from .base import PromptBuilder
from hermes.file_processors.base import FileProcessor
from ..decorators import register_prompt_builder

@register_prompt_builder("xml")
class XMLPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor):
        self.file_processor = file_processor
        self.root = None
        self.erase()

    def add_text(self, text: str, name: Optional[str] = None):
        if name:
            text_elem = ET.SubElement(self.root, "text", name=name)
        else:
            text_elem = ET.SubElement(self.root, "text")
        text_elem.text = text

    def add_file(self, file_path: str, name: str):
        content = self.file_processor.read_file(file_path)
        file_elem = ET.SubElement(self.root, "document", name=name)
        file_elem.text = content

    def add_image(self, image_path: str, name: str):
        raise NotImplementedError("Images are not supported in XML format")

    def build_prompt(self) -> str:
        return ET.tostring(self.root, encoding='unicode')

    def erase(self):
        self.root = ET.Element("input")
        help_content = ET.SubElement(self.root, "text", name="help")
        help_content.text = "This is the user input, it's formatted as XML, and that the assistant will reply to it."
