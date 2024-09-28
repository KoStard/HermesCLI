from argparse import ArgumentParser, Namespace
import argparse
from typing import List
import logging
import os
import glob
import logging
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

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.files:
            self._validate_and_add_files(args.files)
        self.logger.debug(f"Loaded {len(self.file_paths)} file paths from CLI arguments")

    def load_context_from_string(self, new_file_paths: List[str]):
        self._validate_and_add_files(new_file_paths)
        self.logger.debug(f"Added {len(new_file_paths)} file paths interactively")

    def _validate_and_add_files(self, file_paths: List[str]):
        for file_path in file_paths:
            for matched_file in glob.glob(file_path, recursive=True):
                if os.path.exists(matched_file):
                    self.file_paths.append(matched_file)
                    self.logger.info(f"File captured: {matched_file}")
                else:
                    self.logger.warning(f"File not found: {matched_file}")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for file_path in self.file_paths:
            if os.path.isdir(file_path):
                for root, _, files in os.walk(file_path):
                    for file in files:
                        prompt_builder.add_file(os.path.join(root, file), file_utils.process_file_name(file))
            else:
                prompt_builder.add_file(file_path, file_utils.process_file_name(file_path))


    @staticmethod
    def get_command_key() -> List:
        return ["file", "files"]
