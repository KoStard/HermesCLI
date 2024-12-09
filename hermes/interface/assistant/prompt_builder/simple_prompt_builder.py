from .base import PromptBuilder, PromptBuilderFactory
from typing import List

class SimplePromptBuilder(PromptBuilder):
    """A simple prompt builder that concatenates text pieces with empty lines between them."""
    
    def __init__(self):
        self.text_pieces: List[str] = []

    def add_text(self, text: str, name: str = None, text_role: str = None):
        """
        Adds a piece of text to the prompt.
        
        Args:
            text (str): The text to add
            name (str, optional): Name identifier for the text piece (unused in simple builder)
            text_role (str, optional): Role of the text (unused in simple builder)
        """
        self.text_pieces.append(text.strip())

    def compile_prompt(self) -> str:
        """
        Compiles all added text pieces into a single prompt.
        
        Returns:
            str: The compiled prompt with empty lines between text pieces
        """
        if not self.text_pieces:
            return ""
            
        return "\n\n".join(self.text_pieces)


class SimplePromptBuilderFactory(PromptBuilderFactory):
    def create_prompt_builder(self) -> PromptBuilder:
        return SimplePromptBuilder()