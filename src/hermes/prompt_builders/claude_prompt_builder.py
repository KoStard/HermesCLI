import base64
from typing import List, Dict, Any, Optional
from pathlib import Path
from .base import PromptBuilder
from hermes.file_processors.base import FileProcessor

class ClaudePromptBuilder(PromptBuilder):
    def __init__(self, file_processor: FileProcessor):
        self.contents: List[Dict[str, Any]] = []
        self.file_processor = file_processor

    def add_text(self, text: str, name: Optional[str] = None):
        content = {"type": "text", "text": text}
        if name:
            content["text"] = f"{name}:\n{text}"
        self.contents.append(content)

    def add_file(self, file_path: str, name: str):
        # For Claude, we'll treat files as text unless they're images
        file_content = self.file_processor.read_file(file_path)
        if Path(file_path).suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
            self.add_image(file_path, name)
        else:
            self.add_text(f"{name}:\n{file_content.decode('utf-8')}")

    def add_image(self, image_path: str, name: str):
        image_content = self.file_processor.read_file(image_path)
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        media_type = f"image/{Path(image_path).suffix.lower()[1:]}"
        
        self.contents.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_base64
            }
        })

    def build_prompt(self) -> List[Dict[str, Any]]:
        return [{"role": "user", "content": self.contents}]

    def erase(self):
        self.contents = []
