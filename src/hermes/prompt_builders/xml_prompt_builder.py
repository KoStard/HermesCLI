import xml.etree.ElementTree as ET
from typing import Optional
from .base import PromptBuilder
from hermes.file_processors.base import FileProcessor
from ..registry import register_prompt_builder

@register_prompt_builder("xml")
class XMLPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor, author: str, do_introduction: bool = False):
        self.file_processor = file_processor
        self.author = author
        self.do_introduction = do_introduction
        self.root = None
        self.input_elem = None
        self.erase()

    def add_text(self, text: str, name: Optional[str] = None):
        if name:
            text_elem = ET.SubElement(self.input_elem, "text", name=name)
        else:
            text_elem = ET.SubElement(self.input_elem, "text")
        text_elem.text = text

    def add_file(self, file_path: str, name: str):
        content = self.file_processor.read_file(file_path)
        file_elem = ET.SubElement(self.input_elem, "document", name=name)
        file_elem.text = content

    def add_image(self, image_path: str, name: str):
        raise NotImplementedError("Images are not supported in XML format")

    def build_prompt(self) -> str:
        return ET.tostring(self.root, encoding='unicode')

    def erase(self):
        self.root = ET.Element("root")
        help_content = ET.SubElement(self.root, "text", name="help")
        help_content.text = "This XML object represents the request. The user input is located inside the <input> tag, structured as a series of <text> and <document> tags. The content of these tags is the user input. The assistant will generate a response based on this input. Your response should not be formatted as XML, but as plain text, can be markdown."
        self.input_elem = ET.SubElement(self.root, "input")
