import xml.etree.ElementTree as ET
from typing import Optional, List
from .base import PromptBuilder
from hermes.file_processors.base import FileProcessor

class XMLPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor):
        self.root = ET.Element("input")
        self.file_processor = file_processor
        self.text_inputs: List[str] = []

        # Add system message
        system_message = ET.SubElement(self.root, "systemMessage")
        system_message.text = "You are a helpful assistant, helping with the requests your manager will assign to you. You gain bonus at the end of each week if you meaningfully help your manager with his goals."

    def add_text(self, text: str, name: Optional[str] = None):
        if name:
            text_elem = ET.SubElement(self.root, "text", name=name)
        else:
            text_elem = ET.SubElement(self.root, "text")
        text_elem.text = text
        self.text_inputs.append(text)

    def add_file(self, file_path: str, name: str):
        content = self.file_processor.read_file(file_path)
        file_elem = ET.SubElement(self.root, "document", name=name)
        file_elem.text = content

    def add_image(self, image_path: str, name: str):
        image_elem = ET.SubElement(self.root, "image", path=image_path, name=name)

    def build_prompt(self) -> str:
        if self.text_inputs:
            text_inputs_elem = ET.SubElement(self.root, "text_inputs")
            for text in self.text_inputs:
                text_elem = ET.SubElement(text_inputs_elem, "text")
                text_elem.text = text

        return ET.tostring(self.root, encoding='unicode')

    def add_special_command(self, command: str, value: str):
        command_elem = ET.SubElement(self.root, "specialCommand")
        cmd_elem = ET.SubElement(command_elem, command)
        cmd_elem.text = value

        if command == 'append':
            prompt_elem = ET.SubElement(self.root, "prompt")
            prompt_elem.text = f"Please provide only the text that should be appended to the file '{value}'. Do not include any explanations or additional comments."
        elif command == 'update':
            prompt_elem = ET.SubElement(self.root, "prompt")
            prompt_elem.text = f"Please provide the entire new content for the file '{value}'. The output should contain only the new file content, without any explanations or additional comments."

    def add_content(self, content_to_add: str):
        new_content = ET.SubElement(self.root, "additional_content")
        new_content.text = content_to_add
