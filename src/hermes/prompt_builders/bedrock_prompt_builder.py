from typing import Optional, List, Dict, Union, Any

from hermes.file_processors.base import FileProcessor
from .base import PromptBuilder
from hermes.utils.file_utils import is_binary

class BedrockPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor):
        self.contents: List[Dict[str, Union[str, Dict[str, Any]]]] = []
        self.system_message_added = False
        self.file_processor = file_processor

    def add_text(self, text: str, name: Optional[str] = None):
        if not self.system_message_added:
            self.contents.append({
                'text': "You are a helpful assistant, helping with the requests your manager will assign to you. You gain bonus at the end of each week if you meaningfully help your manager with his goals.\n"
            })
            self.system_message_added = True

        content = text if not name else f"{name}:\n{text}"
        self.contents.append({'text': content + '\n'})

    def add_file(self, file_path: str, name: str):
        file_name = name or file_path
        self.contents.append({
            'text': f"File: {file_name}\nContent:\n{{file_content:{file_path}}}\n"
        })

    def add_image(self, image_path: str, name: Optional[str] = None):
        image_name = name or image_path
        self.contents.append({
            'image': {
                'name': image_name,
                'source': {
                    'path': image_path
                }
            }
        })

    def build_prompt(self) -> List[Dict[str, Union[str, Dict[str, Any]]]]:
        return self.contents
