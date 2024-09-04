import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union

from hermes.file_processors.base import FileProcessor
from hermes.utils.file_utils import is_binary

from .base import PromptBuilder


class BedrockPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor):
        self.contents: List[Dict[str, Union[str, Dict[str, Any]]]] = []
        self.file_processor = file_processor

    def add_text(self, text: str, name: Optional[str] = None):
        content = text if not name else f"{name}:\n{text}"
        self.contents.append({'text': content + '\n'})

    def add_file(self, file_path: str, name: str):
        if is_binary(file_path):
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            content_bytes = self.file_processor.read_file(file_path)
            self.contents.append({
                'document': {
                    'format': ext[1:],
                    'name': name,
                    'source': {
                        'bytes': content_bytes
                    }
                }
            })
        else:
            print(f"{file_path} is not binary")
            file_content = self.file_processor.read_file(file_path).decode('utf-8')
            file_elem = ET.Element("document", name=name)
            file_elem.text = file_content
            self.contents.append({'text': ET.tostring(file_elem, encoding='unicode')})

    def add_image(self, image_path: str, name: str):
        _, ext = os.path.splitext(image_path)
        ext = ext.lower()
        content_bytes = self.file_processor.read_file(image_path)
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
