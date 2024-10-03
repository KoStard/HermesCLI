from argparse import ArgumentParser, Namespace
import argparse
from typing import List, Dict, Any
import logging
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TextContextProvider(ContextProvider):
    def __init__(self):
        self.texts: List[str] = []
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('--text', type=str, action='append', help=TextContextProvider.get_help())

    @staticmethod
    def get_help() -> str:
        return 'Text to be included in the context (can be used multiple times)'

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.text:
            self.texts = args.text if isinstance(args.text, list) else [args.text]
        self.logger.debug(f"Loaded {len(self.texts)} text inputs from CLI arguments")

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

    def serialize(self) -> Dict[str, Any]:
        return {
            "texts": self.texts
        }

    def deserialize(self, data: Dict[str, Any]):
        self.texts = data.get("texts", [])
