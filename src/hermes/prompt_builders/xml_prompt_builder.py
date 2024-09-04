import xml.etree.ElementTree as ET
from typing import Optional
from .base import PromptBuilder

class XMLPromptBuilder(PromptBuilder):
    def __init__(self):
        self.root = ET.Element("input")
        self.system_message_added = False

    def add_text(self, text: str, name: Optional[str] = None):
        if not self.system_message_added:
            system_message = ET.SubElement(self.root, "systemMessage")
            system_message.text = "You are a helpful assistant, helping with the requests your manager will assign to you. You gain bonus at the end of each week if you meaningfully help your manager with his goals."
            self.system_message_added = True

        if name:
            text_elem = ET.SubElement(self.root, "text", name=name)
        else:
            text_elem = ET.SubElement(self.root, "text")
        text_elem.text = text

    def add_file(self, file_path: str, name: str):
        file_elem = ET.SubElement(self.root, "document", name=name)
        file_elem.text = f"{{file_content:{file_path}}}"

    def add_image(self, image_path: str, name: str):
        image_elem = ET.SubElement(self.root, "image", path=image_path, name=name)

    def build_prompt(self) -> str:
        return ET.tostring(self.root, encoding='unicode')
