from typing import List
from argparse import ArgumentParser
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class PromptFileContextProvider(ContextProvider):
    def __init__(self):
        self.prompt: str = ""

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--prompt-file", help="File containing prompt to send immediately")

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.prompt_file:
            with open(args.prompt_file, 'r') as f:
                self.prompt = f.read().strip()

    def load_context_from_string(self, args: List[str]):
        if args:
            with open(args[0], 'r') as f:
                self.prompt = f.read().strip()

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.prompt:
            prompt_builder.add_text(self.prompt)

    @staticmethod
    def get_command_key() -> str:
        return "prompt_file"

    def is_used(self) -> bool:
        return bool(self.prompt)

    def get_required_providers(self) -> dict:
        return {}

    def counts_as_input(self) -> bool:
        return True
