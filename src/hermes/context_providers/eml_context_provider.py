import argparse
from typing import List
import logging
import os
import glob
import email
from email import policy
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils

class EMLContextProvider(ContextProvider):
    def __init__(self):
        self.eml_paths: List[str] = []
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: argparse.ArgumentParser):
        parser.add_argument('--eml', nargs='*', help=EMLContextProvider.get_help())

    @staticmethod
    def get_help() -> str:
        return 'EML (email) files to be included in the context'

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.eml:
            self._validate_and_add_eml_files(args.eml)
        self.logger.debug(f"Loaded {len(self.eml_paths)} EML file paths from CLI arguments")

    def load_context_from_string(self, new_eml_paths: List[str]):
        self._validate_and_add_eml_files(new_eml_paths)
        self.logger.debug(f"Added {len(new_eml_paths)} EML file paths interactively")

    def _validate_and_add_eml_files(self, eml_paths: List[str]):
        for eml_path in eml_paths:
            for matched_file in glob.glob(eml_path, recursive=True):
                if os.path.exists(matched_file) and matched_file.lower().endswith('.eml'):
                    self.eml_paths.append(matched_file)
                    self.logger.info(f"EML file captured: {matched_file}")
                else:
                    self.logger.warning(f"Invalid EML file: {matched_file}")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for eml_path in self.eml_paths:
            eml_content = self._parse_eml_file(eml_path)
            prompt_builder.add_text(eml_content, file_utils.process_file_name(eml_path))

    def _parse_eml_file(self, eml_path: str) -> str:
        with open(eml_path, 'rb') as eml_file:
            msg = email.message_from_binary_file(eml_file, policy=policy.default)
        
        parsed_content = []
        parsed_content.append(f"From: {msg['from']}")
        parsed_content.append(f"To: {msg['to']}")
        parsed_content.append(f"Subject: {msg['subject']}")
        parsed_content.append(f"Date: {msg['date']}")
        parsed_content.append("\nBody:")
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    content = part.get_payload(decode=True).decode().strip()
                    if content:
                        parsed_content.append(content)
        else:
            content = msg.get_payload(decode=True).decode().strip()
            if content:
                parsed_content.append(content)
        
        return "\n".join(parsed_content)

    @staticmethod
    def get_command_key() -> List[str]:
        return ["eml"]

    def serialize(self) -> Dict[str, Any]:
        return {
            "eml_paths": self.eml_paths
        }

    def deserialize(self, data: Dict[str, Any]):
        self.eml_paths = data.get("eml_paths", [])
        for eml_path in self.eml_paths:
            eml_content = self._parse_eml_file(eml_path)
            self.logger.info(f"EML file loaded: {eml_path}")
