from argparse import ArgumentParser, Namespace
import argparse
from typing import List
import logging
import os
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.utils import file_utils
import re

class FillGapsContextProvider(ContextProvider):
    def __init__(self):
        self.file_path: str = ""
        self.special_command_prompt: str = ""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--fill-gaps", help="Fill gaps in the specified file")

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.fill_gaps:
            self.file_path = args.fill_gaps
            self._load_special_command_prompt()
            self.logger.debug(f"Loaded fill-gaps context for file: {self.file_path}")

    def load_context_from_string(self, args: List[str]):
        self.file_path = args[0]
        self._load_special_command_prompt()
        self.logger.debug(f"Added fill-gaps context for file: {self.file_path}")

    def _load_special_command_prompt(self):
        special_command_prompts_path = os.path.join(os.path.dirname(__file__), "special_command_prompts.yaml")
        with open(special_command_prompts_path, 'r') as f:
            import yaml
            special_command_prompts = yaml.safe_load(f)
        self.special_command_prompt = special_command_prompts['fill-gaps'].format(
            file_name=file_utils.process_file_name(self.file_path)
        )

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        if self.file_path:
            prompt_builder.add_text(self.special_command_prompt, "fill_gaps_command")
            prompt_builder.add_file(self.file_path, self.file_path)

    @staticmethod
    def get_command_key() -> str:
        return ["fill-gaps", "fill_gaps"]

    def counts_as_input(self) -> bool:
        return True

    def is_action(self):
        return True
    
    def perform_action(self, recent_llm_response: str):
        original_content = file_utils.read_file_content(
            self.file_path
        )
        filled_content = self._fill_gaps(original_content, recent_llm_response)
        file_utils.write_file(
            self.file_path, filled_content, mode="w"
        )
        return f"Gaps filled in {self.file_path}"
    
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
