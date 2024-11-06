from argparse import ArgumentParser, Namespace
import argparse
import yaml
from typing import List, Dict, Any
import logging
import os
from hermes.context_providers.file_context_provider import FileContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils


class AppendContextProvider(FileContextProvider):
    def __init__(self):
        super().__init__()
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
            self._validate_and_add_files([args.append], role="active")
            self._load_special_command_prompt()
            self.logger.debug(f"Loaded append context for file: {args.append}")

    def load_context_from_string(self, args: List[str]):
        file_path = ' '.join(args)
        self._validate_and_add_files([file_path], role="active")
        self._load_special_command_prompt()
        self.logger.debug(f"Added append context for file: {file_path}")

    def _load_special_command_prompt(self):
        special_command_prompts_path = os.path.join(
            os.path.dirname(__file__), "special_command_prompts.yaml"
        )
        with open(special_command_prompts_path, "r") as f:
            special_command_prompts = yaml.safe_load(f)
        self.special_command_prompt = special_command_prompts["append"].format(
            file_name=file_utils.process_file_name(self.file_paths["active"][0])
        )

    @staticmethod
    def get_command_key() -> str:
        return "append"

    def perform_action(self, recent_llm_response: str) -> str:
        file_path = next(iter(self.file_paths["active"]), "")  # Get the first file path
        file_utils.write_file(file_path, "\n" + recent_llm_response, mode="a")
        return f"Content appended to {file_path}"

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["special_command_prompt"] = self.special_command_prompt
        return data

    def deserialize(self, data: Dict[str, Any]):
        super().deserialize(data)
        self.special_command_prompt = data.get("special_command_prompt", "")

    def is_action(self) -> bool:
        return True

    def get_action_instructions(self) -> str:
        return self.special_command_prompt
    
    def get_action_instructions_reduced(self) -> str:
        return "<Reducted Request: You were asked to append to a file, and reply with a specific format. This applies only to the message you replied with, next messages are not affected.>"
