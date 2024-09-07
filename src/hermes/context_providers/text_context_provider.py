from argparse import ArgumentParser
from typing import List
from hermes.config import HermesConfig
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TextContextProvider(ContextProvider):
    def __init__(self):
        self.texts: List[str] = []

    def add_argument(self, parser: ArgumentParser):
        parser.add_argument('--text', type=str, action='append', help='Text to be included in the context (can be used multiple times)')

    def load_context(self, config: HermesConfig):
        self.texts = config.get('text', [])

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for i, text in enumerate(self.texts, 1):
            prompt_builder.add_text(text, name=f"CLI Text Input {i}")
