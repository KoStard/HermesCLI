from typing import Any, Dict, Optional, List
import xml.etree.ElementTree as ET
from .base import PromptFormatter
from hermes.file_processors.base import FileProcessor

class XMLPromptFormatter(PromptFormatter):
    def __init__(self, file_processor: FileProcessor):
        self.file_processor = file_processor

    def format_prompt(self, files: Dict[str, str], prompt: str, special_command: Optional[Dict[str, str]] = None, text_inputs: List[str] = []) -> str:
        root = ET.Element("input")

        prompt_elem = ET.SubElement(root, "systemMessage")
        prompt_elem.text = "You are a helpful assistant, helping with the requests your manager will assign to you. You gain bonus at the end of each week if you meaningfully help your manager with his goals."

        for processed_name, file_path in files.items():
            content = self.file_processor.read_file(file_path)
            file_elem = ET.SubElement(root, "document", name=processed_name)
            file_elem.text = content

        prompt_elem = ET.SubElement(root, "prompt")
        prompt_elem.text = prompt

        if text_inputs:
            text_inputs_elem = ET.SubElement(root, "text_inputs")
            for text in text_inputs:
                text_elem = ET.SubElement(text_inputs_elem, "text")
                text_elem.text = text

        if special_command:
            command_elem = ET.SubElement(root, "specialCommand")
            for key, value in special_command.items():
                cmd_elem = ET.SubElement(command_elem, key)
                cmd_elem.text = value

            if 'append' in special_command:
                prompt_elem = ET.SubElement(root, "prompt")
                prompt_elem.text = f"Please provide only the text that should be appended to the file '{special_command['append']}'. Do not include any explanations or additional comments."
            elif 'update' in special_command:
                prompt_elem = ET.SubElement(root, "prompt")
                prompt_elem.text = f"Please provide the entire new content for the file '{special_command['update']}'. The output should contain only the new file content, without any explanations or additional comments."

        return ET.tostring(root, encoding='unicode')

    def add_content(self, current, content_to_add: str) -> Any:
        return current + '\n\n' + content_to_add
