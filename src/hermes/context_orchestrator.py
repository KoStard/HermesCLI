from argparse import ArgumentParser
from typing import List
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.config import HermesConfig

class ContextOrchestrator:
    def __init__(self, context_providers: List[ContextProvider]):
        self.context_providers = context_providers

    def add_arguments(self, parser: ArgumentParser):
        for provider in self.context_providers:
            provider.add_argument(parser)

    def load_contexts(self, config: HermesConfig):
        for provider in self.context_providers:
            provider.load_context(config)

    def build_prompt(self, prompt_builder: PromptBuilder):
        for provider in self.context_providers:
            provider.add_to_prompt(prompt_builder)
