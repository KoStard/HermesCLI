import argparse
import os
import yaml
from typing import Dict, Any, List
from argparse import ArgumentParser, Namespace
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class PrefillContextProvider(ContextProvider):
    def __init__(self):
        self.prefill_names: List[str] = []
        self.prefill_contents: List[str] = []
        self.required_providers: Dict[str, Any] = {}
        self.prefill_map: Dict[str, str] = {}
        self._load_prefill_map()

    @staticmethod
    def add_argument(parser: ArgumentParser):
        prefills = PrefillContextProvider.get_available_prefills()
        help_text = f"Names of the prefills to use. Available options: {', '.join(prefills)}"
        parser.add_argument('--prefill', action="append", help=help_text)

    @staticmethod
    def get_help() -> str:
        prefills = PrefillContextProvider.get_available_prefills()
        return f"Names of the prefills to use. Available options: {', '.join(prefills)}"

    @staticmethod
    def get_available_prefills() -> List[str]:
        prefill_dirs = [
            os.path.join(os.path.dirname(__file__), "prefills"),  # Repository prefills
            os.path.expanduser("~/.config/hermes/prefills"),
        ]
        prefills = []
        for prefill_dir in prefill_dirs:
            if os.path.exists(prefill_dir):
                prefills.extend([f.split('.')[0] for f in os.listdir(prefill_dir) if f.endswith('.md')])
        return list(set(prefills))

    def _load_prefill_map(self):
        prefill_dirs = [
            os.path.join(os.path.dirname(__file__), "prefills"),  # Repository prefills
            os.path.expanduser("~/.config/hermes/prefills"),
        ]
        for prefill_dir in prefill_dirs:
            if os.path.exists(prefill_dir):
                for filename in os.listdir(prefill_dir):
                    if filename.endswith('.md'):
                        prefill_name = filename.split('.')[0]
                        self.prefill_map[prefill_name] = os.path.join(prefill_dir, filename)

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.prefill:
            self.prefill_names = args.prefill if isinstance(args.prefill, list) else [args.prefill]
            self._load_prefills()

    def load_context_from_string(self, args: List[str]):
        self.prefill_names = [name.strip() for name in args]
        self._load_prefills()

    def _load_prefills(self):
        for prefill_name in self.prefill_names:
            if prefill_name in self.prefill_map:
                self._parse_prefill_file(self.prefill_map[prefill_name])
            else:
                raise ValueError(f"Prefill '{prefill_name}' not found")

    def _parse_prefill_file(self, file_path: str):
        with open(file_path, 'r') as f:
            content = f.read()
            front_matter, prefill_content = content.split('---', 2)[1:]
            metadata = yaml.safe_load(front_matter)
            self.prefill_contents.append(prefill_content.strip())
            self.required_providers.update(metadata.get('required_context_providers', {}))

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for prefill_content in self.prefill_contents:
            prompt_builder.add_text(prefill_content)

    @staticmethod
    def get_command_key() -> str:
        return "prefill"

    def get_required_providers(self) -> Dict[str, List[str]]:
        return self.required_providers
