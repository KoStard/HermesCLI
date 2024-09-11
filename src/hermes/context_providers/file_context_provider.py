from argparse import ArgumentParser
from typing import List
import logging
from hermes.config import HermesConfig
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils.file_utils import process_file_name

class FileContextProvider(ContextProvider):
    def __init__(self):
        self.files: List[str] = []
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('files', nargs='*', help='Files to be included in the context')

    def load_context_from_cli(self, config: HermesConfig):
        self.files = config.get('files', [])
        self.logger.info(f"Loaded {len(self.files)} files from CLI config")

    def load_context_interactive(self, args: str):
        new_files = args.split()
        self.files.extend(new_files)
        self.logger.info(f"Added {len(new_files)} files interactively")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for file_path in self.files:
            prompt_builder.add_file(file_path, process_file_name(file_path))

    @staticmethod
    def get_command_key() -> str:
        return "file"
