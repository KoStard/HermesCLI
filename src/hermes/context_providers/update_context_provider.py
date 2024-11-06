from argparse import ArgumentParser, Namespace
import argparse
import yaml
from typing import Any, Dict, List
import logging
import os
from hermes.context_providers.file_context_provider import FileContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils

class UpdateContextProvider(FileContextProvider):
    def __init__(self):
        super().__init__()
        self.special_command_prompt: str = ""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--update", "--create", "--write", "-u", "-c", "-w", 
                          help=UpdateContextProvider.get_help(), dest="update")

    @staticmethod
    def get_help() -> str:
        return "Update or create the specified file"

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.update:
            self._validate_and_add_files([args.update], role="active")
            self._load_special_command_prompt()
            self.logger.debug(f"Loaded update context for file: {args.update}")

    def load_context_from_string(self, args: List[str]):
        file_path = ' '.join(args)
        self._validate_and_add_files([file_path], role="active")
        self._load_special_command_prompt()
        self.logger.debug(f"Added update context for file: {file_path}")

    def _load_special_command_prompt(self):
        special_command_prompts_path = os.path.join(os.path.dirname(__file__), "special_command_prompts.yaml")
        with open(special_command_prompts_path, 'r') as f:
            special_command_prompts = yaml.safe_load(f)
        self.special_command_prompt = special_command_prompts['update'].format(
            file_name=file_utils.process_file_name(self.file_paths["active"][0])
        )

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.file_paths:
            prompt_builder.add_text(self.special_command_prompt, "update_command")
            super().add_to_prompt(prompt_builder)

    @staticmethod
    def get_command_key() -> List[str]:
        return ["update", "create"]

    def perform_action(self, recent_llm_response: str):
        file_path = next(iter(self.file_paths["active"]), "")  # Get the first file path
        file_utils.write_file(file_path, recent_llm_response, mode="w")
        return f"File {file_path} updated"

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["special_command_prompt"] = self.special_command_prompt
        return data

    def deserialize(self, data: Dict[str, Any]):
        super().deserialize(data)
        self.special_command_prompt = data.get("special_command_prompt", "")
