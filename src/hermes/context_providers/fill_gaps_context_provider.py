from argparse import ArgumentParser, Namespace
import argparse
from typing import List, Dict, Any
import logging
import os
from hermes.context_providers.file_context_provider import FileContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils
import re

class FillGapsContextProvider(FileContextProvider):
    def __init__(self):
        super().__init__()
        self.special_command_prompt: str = ""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--fill-gaps", help=FillGapsContextProvider.get_help())

    @staticmethod
    def get_help() -> str:
        return "Fill gaps in the specified file"

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.fill_gaps:
            self._validate_and_add_files([args.fill_gaps], role="active")
            self._load_special_command_prompt()
            self.logger.debug(f"Loaded fill-gaps context for file: {args.fill_gaps}")

    def load_context_from_string(self, args: List[str]):
        file_path = ' '.join(args)
        self._validate_and_add_files([file_path], role="active")
        self._load_special_command_prompt()
        self.logger.debug(f"Added fill-gaps context for file: {file_path}")

    def _load_special_command_prompt(self):
        special_command_prompts_path = os.path.join(os.path.dirname(__file__), "special_command_prompts.yaml")
        with open(special_command_prompts_path, 'r') as f:
            import yaml
            special_command_prompts = yaml.safe_load(f)
        self.special_command_prompt = special_command_prompts['fill-gaps'].format(
            file_name=file_utils.process_file_name(self.file_paths["active"][0])
        )

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.file_paths:
            prompt_builder.add_text(self.special_command_prompt, "fill_gaps_command")
            super().add_to_prompt(prompt_builder)

    @staticmethod
    def get_command_key() -> str:
        return "fill-gaps"

    def perform_action(self, recent_llm_response: str):
        file_path = next(iter(self.file_paths["active"]), "")  # Get the first file path
        original_content = file_utils.read_file_content(file_path)
        filled_content = self._fill_gaps(original_content, recent_llm_response)
        file_utils.write_file(file_path, filled_content, mode="w")
        return f"Gaps filled in {file_path}"

    def _fill_gaps(self, original_content: str, new_content: str) -> str:
        # Split the original content into lines
        original_lines = original_content.split("\n")

        # Find all gap markers and add indices
        gap_markers = []
        for i, line in enumerate(original_lines):
            if "<GapToFill>" in line:
                gap_markers.append(i)
                original_lines[i] = line.replace(
                    "<GapToFill>", f"<GapToFill index={len(gap_markers)}>"
                )

        # Join the lines with added indices
        indexed_content = "\n".join(original_lines)

        # Send the indexed content to the LLM (this part is handled elsewhere)

        # Extract new content for each gap
        new_content_blocks = re.findall(
            r"<NewGapContent index=(\d+)>(.*?)</NewGapContent>", new_content, re.DOTALL
        )

        # Replace gaps with new content
        for index, content in new_content_blocks:
            index = int(index)
            if index <= len(gap_markers):
                gap_line = gap_markers[index - 1]
                original_lines[gap_line] = (
                    original_lines[gap_line].split("<GapToFill")[0] + content.strip()
                )
        # Join the lines back together
        return "\n".join(original_lines)

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["special_command_prompt"] = self.special_command_prompt
        return data

    def deserialize(self, data: Dict[str, Any]):
        super().deserialize(data)
        self.special_command_prompt = data.get("special_command_prompt", "")
