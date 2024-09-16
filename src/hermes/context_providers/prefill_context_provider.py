import os
import yaml
from typing import Dict, Any
from argparse import ArgumentParser
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.config import HermesConfig

class PrefillContextProvider(ContextProvider):
    def __init__(self):
        self.prefill_name: str = ""
        self.prefill_content: str = ""
        self.required_providers: Dict[str, Any] = {}

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument('--prefill', help='Name of the prefill to use')

    def load_context_from_cli(self, config: HermesConfig):
        self.prefill_name = config.get('prefill')
        if self.prefill_name:
            self._load_prefill()

    def load_context_from_string(self, args: str):
        self.prefill_name = args.strip()
        self._load_prefill()

    def _load_prefill(self):
        prefill_dirs = [
            os.path.join(os.path.dirname(__file__), "..", "prefills"),  # Repository prefills
            os.path.expanduser("~/.config/hermes/prefills"),
            os.path.expanduser("~/.config/hermes/custom_prefills")
        ]

        for prefill_dir in prefill_dirs:
            prefill_path = os.path.join(prefill_dir, f"{self.prefill_name}.md")
            if os.path.exists(prefill_path):
                self._parse_prefill_file(prefill_path)
                return

        raise ValueError(f"Prefill '{self.prefill_name}' not found")

    def _parse_prefill_file(self, file_path: str):
        with open(file_path, 'r') as f:
            content = f.read()
            front_matter, self.prefill_content = content.split('---', 2)[1:]
            metadata = yaml.safe_load(front_matter)
            self.required_providers = metadata.get('required_context_providers', {})

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        prompt_builder.add_text(self.prefill_content)

    @staticmethod
    def get_command_key() -> str:
        return "prefill"

    def is_used(self) -> bool:
        return bool(self.prefill_name)

    def get_required_providers(self) -> Dict[str, Any]:
        return self.required_providers
