from argparse import ArgumentParser
from typing import List
import logging
import os
from hermes.config import HermesConfig
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils

class FileContextProvider(ContextProvider):
    def __init__(self):
        self.file_paths: List[str] = []
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('files', nargs='*', help='Files to be included in the context')

    def load_context_from_cli(self, config: HermesConfig):
        file_paths = config.get('files', [])
        self._validate_and_add_files(file_paths)
        self.logger.info(f"Loaded {len(self.file_paths)} file paths from CLI config")

    def load_context_interactive(self, args: str):
        new_file_paths = [args]
        self._validate_and_add_files(new_file_paths)
        self.logger.info(f"Added {len(new_file_paths)} file paths interactively")

    def _validate_and_add_files(self, file_paths: List[str]):
        for file_path in file_paths:
            if os.path.exists(file_path):
                self.file_paths.append(file_path)
            else:
                self.logger.warning(f"File not found: {file_path}")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for file_path in self.file_paths:
            prompt_builder.add_file(file_path, file_utils.process_file_name(file_path))


    @staticmethod
    def get_command_key() -> str:
        return "file"

    def is_used(self) -> bool:
        return len(self.file_paths) > 0
