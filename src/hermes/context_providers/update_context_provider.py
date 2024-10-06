from argparse import ArgumentParser, Namespace
import argparse
import yaml
from typing import Any, Dict, List
import logging
import os
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils

class UpdateContextProvider(ContextProvider):
    def __init__(self):
        self.file_path: str = ""
        self.special_command_prompt: str = ""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--update", "--create", "--write", "-u", "-c", "-w", help=UpdateContextProvider.get_help(), dest="update")

    @staticmethod
    def get_help() -> str:
        return "Update or create the specified file"

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.update:
            self.file_path = args.update
            self._load_special_command_prompt()
            self.logger.debug(f"Loaded update context for file: {self.file_path}")

    def load_context_from_string(self, args: List[str]):
        self.file_path = ' '.join(args)
        self._load_special_command_prompt()
        self.logger.debug(f"Added update context for file: {self.file_path}")

    def _load_special_command_prompt(self):
        special_command_prompts_path = os.path.join(os.path.dirname(__file__), "special_command_prompts.yaml")
        with open(special_command_prompts_path, 'r') as f:
            special_command_prompts = yaml.safe_load(f)
        self.special_command_prompt = special_command_prompts['update'].format(
            file_name=file_utils.process_file_name(self.file_path)
        )

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.file_path:
            prompt_builder.add_text(self.special_command_prompt, "update_command")
            prompt_builder.add_file(self.file_path, self.file_path)

    @staticmethod
    def get_command_key() -> List[str]:
        return ["update", "create"]

    def counts_as_input(self) -> bool:
        return True

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        return {
            self.get_command_key(): {
                "texts": self.texts
            }
        }

    def deserialize(self, data: Dict[str, Any]):
        self.texts = data.get("texts", [])

    def is_action(self):
        return True
    
    def perform_action(self, recent_llm_response: str):
        file_utils.write_file(self.file_path, recent_llm_response, mode="w")
        return f"File {self.file_path} updated"
    def serialize(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "special_command_prompt": self.special_command_prompt
        }

    def deserialize(self, data: Dict[str, Any]):
        self.file_path = data.get("file_path", "")
        self.special_command_prompt = data.get("special_command_prompt", "")
