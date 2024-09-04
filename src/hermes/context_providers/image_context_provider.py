import base64
from argparse import ArgumentParser
from typing import List, Optional
from PIL import Image
import io

from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class ImageContextProvider(ContextProvider):
    def __init__(self):
        self.image_paths: List[str] = []
        self.image_contents: List[str] = []

    def add_argument(self, parser: ArgumentParser):
        parser.add_argument("--image", action="append", help="Path to image file to include in the context")

    def load_context(self, args):
        if args.image:
            self.image_paths = args.image
            for image_path in self.image_paths:
                content = self.process_image(image_path)
                self.image_contents.append(content)

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for image_path, content in zip(self.image_paths, self.image_contents):
            prompt_builder.add_image(content, name=f"Image: {image_path}")

    def process_image(self, image_path: str) -> str:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
