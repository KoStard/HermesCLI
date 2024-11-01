import base64
from typing import List, Dict, Any, Optional
from pathlib import Path
from .base import PromptBuilder
from hermes.file_processors.base import FileProcessor
from ..registry import register_prompt_builder

@register_prompt_builder("openai")
class OpenAIPromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor, author: str, do_introduction: bool = False):
        self.contents: List[Dict[str, Any]] = []
        self.file_processor = file_processor
        self.author = author
        self.do_introduction = do_introduction

    def add_text(self, text: str, name: Optional[str] = None):
        content = {"type": "text", "text": text}
        if name:
            content["text"] = f"{name}:\n{text}"
        self.contents.append(content)

    def add_file(self, file_path: str, name: str, role: str = None):
        # For OpenAI, we'll treat files as text unless they're images
        if Path(file_path).suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
            self.add_image(file_path, name)
            return
        file_content = self.file_processor.read_file(file_path)
        role_info = f"Role: {role}\n" if role else ""
        self.add_text(f"{role_info}{file_content}", name)

    def add_image(self, image_path: str, name: str=None):
        with open(image_path, 'rb') as f:
            image_content = f.read()
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        self.contents.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{Path(image_path).suffix.lower()[1:]};base64,{image_base64}"
            }
        })

    def build_prompt(self) -> List[Dict[str, Any]]:
        return self.contents

    def erase(self):
        self.contents = []
