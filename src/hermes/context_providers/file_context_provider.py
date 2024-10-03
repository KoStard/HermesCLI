from argparse import ArgumentParser, Namespace
import argparse
from typing import List, Dict, Any
import logging
import os
import glob
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils

class FileContextProvider(ContextProvider):
    def __init__(self):
        self.file_paths: List[str] = []
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('files', nargs='*', help=FileContextProvider.get_help())

    @staticmethod
    def get_help() -> str:
        return 'Files or folders to be included in the context'

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.files:
            self._validate_and_add_files(args.files)
        self.logger.debug(f"Loaded {len(self.file_paths)} file/folder paths from CLI arguments")

    def load_context_from_string(self, new_file_paths: List[str]):
        self._validate_and_add_files(new_file_paths)
        self.logger.debug(f"Added {len(new_file_paths)} file/folder paths interactively")

    def _validate_and_add_files(self, file_paths: List[str]):
        for file_path in file_paths:
            matched_paths = glob.glob(file_path, recursive=True)
            if not matched_paths:
                self.logger.warning(f"Invalid path: {file_path}")
            for matched_path in matched_paths:
                self.file_paths.append(matched_path)
                if os.path.isdir(matched_path):
                    self.logger.info(f"Folder captured: {matched_path}")
                else:
                    self.logger.info(f"File captured: {matched_path}")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for path in self.file_paths:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        prompt_builder.add_file(file_path, file_utils.process_file_name(file_path))
            else:
                prompt_builder.add_file(path, file_utils.process_file_name(path))

    @staticmethod
    def get_command_key() -> List[str]:
        return ["file", "files"]

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        return {
            self.get_command_key()[0]: {
                "file_paths": self.file_paths
            }
        }

    def deserialize(self, data: Dict[str, Any]):
        if "file_paths" in data:
            self._validate_and_add_files(data["file_paths"])
        else:
            self.logger.warning("No file paths found in deserialization data")
