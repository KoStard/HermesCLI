from argparse import ArgumentParser, Namespace
import argparse
from typing import List
import logging
import os
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils


class AppendContextProvider(ContextProvider):
    def __init__(self):
        self.file_path: str = ""
        self.special_command_prompt: str = ""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--append", "-a", help=AppendContextProvider.get_help())

    @staticmethod
    def get_help() -> str:
        return "Append to the specified file"

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.append:
            self.file_path = args.append
            self._load_special_command_prompt()
            self.logger.debug(f"Loaded append context for file: {self.file_path}")

    def load_context_from_string(self, args: List[str]):
        self.file_path = args[0]
        self._load_special_command_prompt()
        self.logger.debug(f"Added append context for file: {self.file_path}")

    def _load_special_command_prompt(self):
        special_command_prompts_path = os.path.join(
            os.path.dirname(__file__), "special_command_prompts.yaml"
        )
        with open(special_command_prompts_path, "r") as f:
            import yaml

            special_command_prompts = yaml.safe_load(f)
        self.special_command_prompt = special_command_prompts["append"].format(
            file_name=file_utils.process_file_name(self.file_path)
        )

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.file_path:
            prompt_builder.add_text(self.special_command_prompt, "append_command")
            prompt_builder.add_file(
                self.file_path, file_utils.process_file_name(self.file_path)
            )

    @staticmethod
    def get_command_key() -> str:
        return "append"

    def counts_as_input(self) -> bool:
        return True

    def is_action(self):
        return True

    def perform_action(self, recent_llm_response: str) -> str:
        file_utils.write_file(self.file_path, "\n" + recent_llm_response, mode="a")
        return f"Content appended to {self.file_path}"
