from argparse import ArgumentParser
from typing import List
from hermes.config import HermesConfig
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils.file_utils import process_file_name

class FileContextProvider(ContextProvider):
    def __init__(self):
        self.files: List[str] = []

    def add_argument(self, parser: ArgumentParser):
        parser.add_argument('files', nargs='*', help='Files to be included in the context')

    def load_context(self, config: HermesConfig):
        self.files = config.get('files', [])

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for file_path in self.files:
            prompt_builder.add_file(file_path, process_file_name(file_path))
