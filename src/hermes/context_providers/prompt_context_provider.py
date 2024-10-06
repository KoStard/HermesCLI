import argparse
from typing import List, Dict, Any
from argparse import ArgumentParser, Namespace
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class PromptContextProvider(ContextProvider):
    def __init__(self):
        self.prompt: str = ""

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--prompt", help=PromptContextProvider.get_help())

    @staticmethod
    def get_help() -> str:
        return "Prompt text to send immediately"

    def load_context_from_cli(self, args: argparse.Namespace):
        self.prompt = args.prompt if args.prompt else ""

    def load_context_from_string(self, args: List[str]):
        self.prompt = " ".join(args)

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.prompt:
            prompt_builder.add_text(self.prompt)

    @staticmethod
    def get_command_key() -> str:
        return "prompt"

    def get_required_providers(self) -> dict:
        return {}

    def counts_as_input(self) -> bool:
        return True

    def serialize(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt
        }

    def deserialize(self, data: Dict[str, Any]):
        self.prompt = data.get("prompt", "")
