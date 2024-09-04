from abc import ABC, abstractmethod
from argparse import ArgumentParser
from typing import TypeVar, Any

from hermes.prompt_builders.base import PromptBuilder

T = TypeVar('T')  # Define a type variable

class ContextProvider(ABC):
    @abstractmethod
    def add_argument(self, parser: ArgumentParser):
        """
        Add the necessary arguments to the ArgumentParser.
        
        :param parser: The ArgumentParser to add arguments to
        """
        pass

    @abstractmethod
    def load_context(self, args: Any):
        """
        Load and process the context from the parsed arguments.
        
        :param args: The parsed arguments from ArgumentParser
        """
        pass

    @abstractmethod
    def add_to_prompt(self, prompt_builder: PromptBuilder):
        """
        Add the loaded context to the prompt builder.
        
        :param prompt_builder: The PromptBuilder instance to add context to
        """
        pass
