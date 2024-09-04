from argparse import ArgumentParser
from typing import Any
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TextContextProvider(ContextProvider):
    def __init__(self):
        self.text: str = ""

    def add_argument(self, parser: ArgumentParser):
        parser.add_argument('--text', type=str, help='Text to be included in the context')

    def load_context(self, args: Any):
        self.text = args.text if args.text else ""

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.text:
            prompt_builder.add_text(self.text, name="CLI Text Input")
