from argparse import ArgumentParser, Namespace
import argparse
from typing import List, Dict, Any
import logging
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TextContextProvider(ContextProvider):
    def __init__(self):
        self.texts: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('--text', type=str, action='append', help=TextContextProvider.get_help())

    @staticmethod
    def get_help() -> str:
        return 'Text to be included in the context (can be used multiple times)'

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.text:
            cli_texts = args.text if isinstance(args.text, list) else [args.text]
            self.texts["CLI Text Input"] = self.texts.get("CLI Text Input", []) + cli_texts
        self.logger.debug(f"Loaded {len(self.texts.get('CLI Text Input', []))} text inputs from CLI arguments")

    def load_context_from_string(self, args: List[str]):
        if not args:
            return
        text = " ".join(args)
        self.texts["Text Input"] = self.texts.get("Text Input", []) + [text]
        self.logger.debug(f"Added {len(args)} text input interactively")

    def add_text(self, text: str, name: str):
        self.texts[name] = self.texts.get(name, []) + [text]
        self.logger.debug(f"Added text input with name '{name}'")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for name, texts in self.texts.items():
            for i, text in enumerate(texts, 1):
                prompt_builder.add_text(text, name=f"{name} {i}")

    @staticmethod
    def get_command_key() -> str:
        return "text"

    def serialize(self) -> Dict[str, Any]:
        return {
            "texts": self.texts
        }

    def deserialize(self, data: Dict[str, Any]):
        if isinstance(data, list):
            self.texts = {"CLI Text Input": data}
        self.texts = data.get("texts", {})
