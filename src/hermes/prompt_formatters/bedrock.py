import os
from typing import Any, Dict, List, Optional, Union
import xml.etree.ElementTree as ET
from .base import PromptFormatter
from hermes.file_processors.base import FileProcessor
from hermes.utils.file_utils import is_binary

class BedrockPromptFormatter(PromptFormatter):
    def __init__(self, file_processor: FileProcessor):
        self.file_processor = file_processor

    def format_prompt(self, files: Dict[str, str], prompt: str, special_command: Optional[Dict[str, str]] = None, text_inputs: List[str] = []) -> List[Dict[str, Union[str, Dict[str, Any]]]]:
        contents = []

        for processed_name, file_path in files.items():
            if is_binary(file_path):
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                content_bytes = self.file_processor.read_file(file_path)
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                    print(f"Adding image {file_path} with format {ext}")
                    contents.append({
                        'image': {
                            'format': ext[1:],
                            'source': {
                                'bytes': content_bytes
                            }
                        }
                    })
                else:
                    print(f"Adding document {processed_name} with format {ext}")
                    contents.append({
                        'document': {
                            'format': ext[1:],
                            'name': processed_name,
                            'source': {
                                'bytes': content_bytes
                            }
                        }
                    })
            else:
                print(f"{file_path} is not binary")
                file_content = self.file_processor.read_file(file_path).decode('utf-8')
                file_elem = ET.Element("document", name=processed_name)
                file_elem.text = file_content
                contents.append({'text': ET.tostring(file_elem, encoding='unicode')})
        contents.append({'text': prompt + '\n'})

        if text_inputs:
            text_inputs_content = "Additional text inputs:\n"
            for text in text_inputs:
                text_inputs_content += f"{text}\n"
            contents.append({'text': text_inputs_content})

        if text_inputs:
            prompt += "Additional text inputs:\n"
            for text in text_inputs:
                prompt += f"{text}\n"

        if special_command:
            special_prompt = ""
            if 'append' in special_command:
                special_prompt = f"Please provide only the text that should be appended to the file '{special_command['append']}'. Do not include any explanations or additional comments."
            elif 'update' in special_command:
                special_prompt = f"Please provide the entire new content for the file '{special_command['update']}'. The output should contain only the new file content, without any explanations or additional comments."
            if special_prompt:
                contents.append({'text': special_prompt + '\n'})
        return contents

    def add_content(self, current, content_to_add: str) -> Any:
        return [*current, {'text': content_to_add + '\n'}]
