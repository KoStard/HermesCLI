from argparse import ArgumentParser
from typing import List
import logging

from hermes.config import HermesConfig
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class ImageContextProvider(ContextProvider):
    def __init__(self):
        self.image_paths: List[str] = []
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--image", action="append", help="Path to image file to include in the context")

    def load_context_from_cli(self, config: HermesConfig):
        self.image_paths = config.get('image', [])
        self.logger.info(f"Loaded {len(self.image_paths)} image paths from CLI config")

    def load_context_interactive(self, args: str):
        new_paths = [args]
        self.image_paths.extend(new_paths)
        self.logger.info(f"Added {len(new_paths)} image paths interactively")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for image_path in self.image_paths:
            prompt_builder.add_image(image_path, name=f"Image: {image_path}")

    @staticmethod
    def get_command_key() -> str:
        return "image"
