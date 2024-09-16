from argparse import ArgumentParser
from typing import List
import logging
from hermes.config import HermesConfig
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TextContextProvider(ContextProvider):
    def __init__(self):
        self.texts: List[str] = []
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('--text', type=str, action='append', help='Text to be included in the context (can be used multiple times)')

    def load_context_from_cli(self, config: HermesConfig):
        self.texts = config.get('text', [])
        self.logger.debug(f"Loaded {len(self.texts)} text inputs from CLI config")

    def load_context_from_string(self, args: List[str]):
        if not args:
            return
        self.texts.extend(args)
        self.logger.debug(f"Added {len(args)} text input interactively")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for i, text in enumerate(self.texts, 1):
            prompt_builder.add_text(text, name=f"CLI Text Input {i}")

    @staticmethod
    def get_command_key() -> str:
        return "text"

    def is_used(self) -> bool:
        return len(self.texts) > 0
