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
        self._instructions_context_provider = TextContextProvider()
        self._instructions_context_provider.add_text(self._get_instructions(), "LiveFileInstructions")

    def get_live_diff_snapshot(self) -> List[ContextProvider]:
        current_content = self.get_current_content()

        diff = self._generate_diff(self.last_content, current_content)
        if not diff:
            return []

        self.last_content = current_content

        return [self._generate_diff_context_provider(diff)]

    def get_current_content(self) -> str:
        with open(self.file_path, 'r') as f:
            return f.read()

    def _generate_diff(self, old_content: str, new_content: str) -> List[str]:
        return '\n'.join(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"Previous {self.file_path}",
            tofile=f"Current {self.file_path}",
            lineterm=''
        ))
    
    def _generate_diff_context_provider(self, diff: str) -> TextContextProvider:
        text_context_provider = TextContextProvider()
        text_context_provider.add_text(diff, "LiveFileDiff")
        return text_context_provider

    def _get_instructions(self) -> str:
        return f"""
The user is working on a live file at {self.file_path}. The most current version of the file 
is always available to you. 
The edit history (diffs) for this file is included in the chat history. If there are no diffs, then the document has not been modified after the chat started. 
The user is updating the document based on your interactions. When the user is asking generic questions, check the other documents and not the live document!
Think about the live document as an output of your chat with the user, and not an input, unless directly asked to answer based on that.
It's shared with you, as this way you can know what is the user focused on at the moment and focus your thinking on that.
"""

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
        self._instructions_context_provider.add_to_prompt(prompt_builder)
        prompt_builder.add_file(self.file_path, '[LIVE DOCUMENT] ' + file_utils.process_file_name(self.file_path))

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

