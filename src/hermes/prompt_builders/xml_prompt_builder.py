import xml.etree.ElementTree as ET
from typing import Optional
from .base import PromptBuilder
from hermes.file_processors.base import FileProcessor

class XMLPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor):
        self.root = ET.Element("input")
        self.file_processor = file_processor

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
        image_elem = ET.SubElement(self.root, "image", path=image_path, name=name)

    def build_prompt(self) -> str:
        return ET.tostring(self.root, encoding='unicode')
