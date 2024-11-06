from argparse import ArgumentParser, Namespace, Action
import argparse
from typing import List, Dict, Any, DefaultDict
from collections import defaultdict
import logging
import os
import glob
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils
import textwrap

class FileContextProvider(ContextProvider):
    FILE_ROLES = ['system', 'context', 'active']

    def __init__(self):
        self.file_paths: DefaultDict[str, List[str]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
        
    def get_instructions(self):
        return textwrap.dedent("""
            File roles determine how the content is used in the conversation:

            1. system: These files provide foundational information or rules that guide your behavior 
               throughout the entire conversation. They set the tone and framework for the interaction.

            2. context: These files offer background information or additional context that's relevant to 
               the current conversation but may not be directly part of the main topic or query.

            3. active: These are the primary files being worked on in the current conversation. 
               They are the main focus of the interaction and any changes or analyses typically center 
               around these files. When asked generic questions, normally avoid these files, check the context files.
               The reason for that is that these are the actively modified files, they contain the results of the conversation
               not the input of it.
               Sometimes, you might be directly asked to answer based on these files, in that case check this as well.

            When reading files, pay attention to their roles as it shows the user's intents. 
        """)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        # Add the default files argument
        parser.add_argument('files', nargs='*', help=FileContextProvider.get_help())
        
        # Add role-specific file arguments
        for role in FileContextProvider.FILE_ROLES:
            parser.add_argument(f'--file:{role}', 
                                nargs='+',
                                help=f'Files to be included as {role} role. Multiple files can be specified.')

    @staticmethod
    def get_help() -> str:
        return 'Files or folders to be included in the context'

    def load_context_from_cli(self, args: argparse.Namespace):
        # Handle default files (no role)
        if args.files:
            self._validate_and_add_files(args.files)
        
        # Handle role-specific files
        for role in FileContextProvider.FILE_ROLES:
            role_args = getattr(args, f'file:{role}', None)
            if not role_args:
                continue
            self._validate_and_add_files(role_args, role=role)
        
        total_files = sum(len(files) for files in self.file_paths.values())
        self.logger.debug(f"Loaded {total_files} file/folder paths from CLI arguments")

    def load_context_from_string(self, new_file_paths: List[str]):
        self._validate_and_add_files(new_file_paths)
        self.logger.debug(f"Added {len(new_file_paths)} file/folder paths interactively")

    def _validate_and_add_files(self, file_paths: List[str], role: str = "context"):
        for file_path in file_paths:
            matched_paths = glob.glob(file_path, recursive=True)
            if not matched_paths:
                self.logger.warning(f"Invalid path: {file_path}")
                if not file_path.endswith('/'):
                    # Adding invalid path as a file, so that it's clear that the file doesn't exist (maybe intentional)
                    self.file_paths[role].append(file_path)
            for matched_path in matched_paths:
                self.file_paths[role].append(matched_path)
                role_str = f" as {role}" if role else ""
                if os.path.isdir(matched_path):
                    self.logger.info(f"Folder captured{role_str}: {matched_path}")
                else:
                    self.logger.info(f"File captured{role_str}: {matched_path}")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for role, paths in self.file_paths.items():
            for path in paths:
                if os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            prompt_builder.add_file(file_path, file_utils.process_file_name(file_path), role=role)
                else:
                    prompt_builder.add_file(path, file_utils.process_file_name(path), role=role)

    @staticmethod
    def get_command_key() -> List[str]:
        return ["file", "files", *[f"file:{role}" for role in FileContextProvider.FILE_ROLES]]
    
    def serialize(self) -> Dict[str, Any]:
        return {
            "file_paths": {role: paths for role, paths in self.file_paths.items()}
        }

    def deserialize(self, data: Dict[str, Any]):
        if "file_paths" in data:
            for role, paths in data["file_paths"].items():
                self._validate_and_add_files(paths, role=role)
        else:
            self.logger.warning("No file paths found in deserialization data")
