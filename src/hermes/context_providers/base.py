from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
import argparse
from typing import List, TypeVar, Any, Dict

from hermes.prompt_builders.base import PromptBuilder
T = TypeVar('T')  # Define a type variable

class ContextProvider(ABC):
    @staticmethod
    @abstractmethod
    def add_argument(parser: ArgumentParser):
        """
        Add the necessary arguments to the ArgumentParser.
        
        :param parser: The ArgumentParser to add arguments to
        """
        pass

    @staticmethod
    @abstractmethod
    def get_help() -> str:
        """
        Return the help text for this context provider.
        
        :return: A string containing the help text
        """
        pass

    @abstractmethod
    def load_context_from_cli(self, args: argparse.Namespace):
        """
        Load and process the context from the CLI arguments.
        
        :param args: The parsed command-line arguments
        """
        pass

    @abstractmethod
    def load_context_from_string(self, args: List[str]):
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

    def counts_as_input(self) -> bool:
        """
        Return True if this context provider should be considered as user input.
        
        :return: A boolean indicating whether this provider counts as input
        """
        return False
    
    def is_action(self) -> bool:
        """
        Return True if this context provider represents an action to be performed.

        :return: A boolean indicating whether this provider represents an action
        """
        return False
    
    def perform_action(self, recent_llm_response: str):
        if not self.is_action():
            raise ValueError("This context provider does not represent an action.")
        pass

    @abstractmethod
    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """
        Serialize the context provider's state to a dictionary.

        :return: A dictionary with the format {providerKey: {providerContext}}
        """
        pass

    @abstractmethod
    def deserialize(self, data: Dict[str, Any]):
        """
        Deserialize the given data and set up the context provider's inner state.

        :param data: A dictionary containing the serialized state of the context provider
        """
        pass

    @abstractmethod
    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """
        Serialize the context provider's state to a dictionary.

        :return: A dictionary with the format {providerKey: {providerContext}}
        """
        pass

    @abstractmethod
    def deserialize(self, data: Dict[str, Any]):
        """
        Deserialize the given data and set up the context provider's inner state.

        :param data: A dictionary containing the serialized state of the context provider
        """
        pass
