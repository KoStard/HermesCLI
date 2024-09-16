from typing import List
from argparse import ArgumentParser
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.config import HermesConfig

class PromptContextProvider(ContextProvider):
    def __init__(self):
        self.prompt: str = ""

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--prompt", help="Prompt text to send immediately")

    def load_context_from_cli(self, config: HermesConfig):
        self.prompt = config.get('prompt', [''])[0]

    def load_context_from_string(self, args: List[str]):
        self.prompt = args[0] if args else ""

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.prompt:
            prompt_builder.add_text(self.prompt)

    @staticmethod
    def get_command_key() -> str:
        return "prompt"

    def is_used(self) -> bool:
        return bool(self.prompt)

    def get_required_providers(self) -> dict:
        return {}
