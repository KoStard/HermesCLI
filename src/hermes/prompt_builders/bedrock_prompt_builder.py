import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union

from hermes.file_processors.base import FileProcessor

from .base import PromptBuilder
from ..decorators import register_prompt_builder

@register_prompt_builder("bedrock")
class BedrockPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor):
        self.contents: List[Dict[str, Union[str, Dict[str, Any]]]] = []
        self.file_processor = file_processor

    def add_text(self, text: str, name: Optional[str] = None):
        content = text if not name else f"{name}:\n{text}"
        self.contents.append({'text': content + '\n'})

    def add_file(self, file_path: str, name: str):
        file_content = self.file_processor.read_file(file_path)
        if not file_content:
            print(f"{file_path} could not be processed")
            return
        file_elem = ET.Element("document", name=name)
        file_elem.text = file_content
        self.contents.append({'text': ET.tostring(file_elem, encoding='unicode')})

    def add_image(self, image_path: str, name: str):
        _, ext = os.path.splitext(image_path)
        ext = ext.lower()
        with open(image_path, 'rb') as f:
            content_bytes = f.read()
        self.contents.append({
            'image': {
                'format': ext[1:],
                'source': {
                    'bytes': content_bytes
                }
            }
        })

    def build_prompt(self) -> List[Dict[str, Union[str, Dict[str, Any]]]]:
        return self.contents

    def erase(self):
        self.contents = []
