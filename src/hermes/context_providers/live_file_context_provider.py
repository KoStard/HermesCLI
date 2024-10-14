from argparse import ArgumentParser, Namespace
import os
import difflib
import logging
from typing import Dict, Optional, List

from hermes.context_providers.base import LiveContextProvider, ContextProvider
from hermes.context_providers.text_context_provider import TextContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils

class LiveFileContextProvider(LiveContextProvider):
    def __init__(self):
        self.file_path: Optional[str] = None
        self.last_content: Optional[str] = None
        self.logger = logging.getLogger(__name__)

    def get_live_diff_snapshot(self) -> List[ContextProvider]:
        current_content = self.get_current_content()

        diff = self.generate_diff(self.last_content, current_content)
        if not diff:
            return []

        self.last_content = current_content

        text_context_provider = TextContextProvider()
        text_context_provider.load_context_from_string([diff])

        return [text_context_provider]

    def get_current_content(self) -> str:
        with open(self.file_path, 'r') as f:
            return f.read()

    def generate_diff(self, old_content: str, new_content: str) -> List[str]:
        return '\n'.join(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"Previous {self.file_path}",
            tofile=f"Current {self.file_path}",
            lineterm=''
        ))

    def get_instructions(self) -> str:
        return (
            f"You are working with a live file at {self.file_path}. The most current version of the file "
            "is always available through the regular file context provider. "
            "The edit history (diffs) for this file is included in the chat history. "
            "Please consider both the current state and the recent changes when responding."
        )

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('--live-file', type=str, help=LiveFileContextProvider.get_help())

    @staticmethod
    def get_help() -> str:
        return "Path to a file to watch for changes"

    def load_context_from_cli(self, args: Namespace):
        self._validate_and_save_file_path(args.live_file)

    def load_context_from_string(self, args: List[str]):
        self._validate_and_save_file_path(args[0])

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        prompt_builder.add_text(self.get_instructions())
        prompt_builder.add_file(self.file_path, file_utils.process_file_name(self.file_path))

    @staticmethod
    def get_command_key() -> List[str]:
        return ["live-file", "live_file"]

    def serialize(self) -> Dict[str, str]:
        return {
            "file_path": self.file_path
        }

    def deserialize(self, data: Dict[str, str]):
        self.file_path = data["file_path"]

    def _validate_and_save_file_path(self, file_path: str):
        if not os.path.exists(file_path):
            raise ValueError(f"File path does not exist: {file_path}")

        if os.path.isdir(file_path):
            raise ValueError(f"File path is a directory: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"File path is not a file: {file_path}")

        self.file_path = file_path
        self.last_content = self.get_current_content()
        self.logger.info(f"Live file captured: {file_path}")

