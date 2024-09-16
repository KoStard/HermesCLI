from abc import ABC, abstractmethod
from argparse import ArgumentParser
from typing import List, TypeVar, Any, Dict

from hermes.prompt_builders.base import PromptBuilder
from hermes.config import HermesConfig

T = TypeVar('T')  # Define a type variable

class ContextProvider(ABC):
    @abstractmethod
    def is_used(self) -> bool:
        """
        Return True if the context provider has non-empty values that will add meaningful prompt.
        """
        pass
    @staticmethod
    @abstractmethod
    def add_argument(parser: ArgumentParser):
        """
        Add the necessary arguments to the ArgumentParser.
        
        :param parser: The ArgumentParser to add arguments to
        """
        pass

    @abstractmethod
    def load_context_from_cli(self, config: HermesConfig):
        """
        Load and process the context from the CLI config.
        
        :param config: The HermesConfig object
        """
        pass

    @abstractmethod
    def load_context_from_string(self, args: str):
        """
        Load and process the context from interactive input.
        
        :param args: The arguments provided by the user in the interactive mode
        """
        pass

    @abstractmethod
    def add_to_prompt(self, prompt_builder: PromptBuilder):
        """
        Add the loaded context to the prompt builder.
        
        :param prompt_builder: The PromptBuilder instance to add context to
        """
        pass

    @staticmethod
    @abstractmethod
    def get_command_key() -> str | List[str]:
        """
        Return a key suitable for the context provider without the leading slash.
        
        :return: A string representing the command key for this context provider
        """
        pass

    def get_required_providers(self) -> Dict[str, Any]:
        """
        Return a dictionary of required context providers and their arguments.
        
        :return: A dictionary where keys are provider names and values are their arguments
        """
        return {}
