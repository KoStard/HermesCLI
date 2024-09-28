import argparse
from argparse import ArgumentParser
from typing import Any, Dict, List

from hermes.context_providers import ContextProvider, get_all_context_providers
from hermes.prompt_builders.base import PromptBuilder


class HelpContextProvider(ContextProvider):
    def __init__(self):
        self.loaded = False
        self.help_request: List[str] | None = None

    @staticmethod
    def add_argument(parser: ArgumentParser):
        raise NotImplementedError("HelpContextProvider does not support CLI use case, use argparser help")
    
    def load_context_from_cli(self, args: argparse.Namespace):
        raise NotImplementedError("HelpContextProvider does not support CLI use case, use argparser help")
    
    def load_context_from_string(self, args: List[str]):
        self.loaded = True
        self.help_request = ' '.join(args)
    
    def add_to_prompt(self, prompt_builder: PromptBuilder):
        self._validate_loaded()
        help_content = self._generate_simple_help_content()
        if self._is_simple_mode():
            print(help_content)
        prompt_builder.add_text(help_content)
        if not self._is_simple_mode():
            prompt_builder.add_text(self.help_request)
            
    
    def get_command_key() -> str | List[str]:
        return "help"
    
    def get_required_providers(self) -> Dict[str, Any]:
        self._validate_loaded()
        if self._is_simple_mode():
            return {}
        return {
            'prefill': [
                'hermes_assistant'
            ]
        }
    
    def counts_as_input(self) -> bool:
        self._validate_loaded()
        return not self._is_simple_mode()
    
    def _validate_loaded(self):
        if not self.loaded:
            raise ValueError("HelpContextProvider must be loaded before use")
    
    def _is_simple_mode(self):
        return not self.help_request
        
    def _generate_simple_help_content(self) -> str:
        # programmatically generate help for all available commands
        pass
    