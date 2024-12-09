import textwrap
from .base import PromptBuilder, PromptBuilderFactory
from typing import List


class SimplePromptTextPiece:
    def __init__(self, text: str, name: str = None, text_role: str = None):
        self.text = text
        self.name = name
        self.text_role = text_role

class SimplePromptBuilder(PromptBuilder):
    """A simple prompt builder that concatenates text pieces with empty lines between them."""
    
    def __init__(self):
        self.text_pieces: List[SimplePromptTextPiece] = []

    def add_text(self, text: str, name: str = None, text_role: str = None):
        """
        Adds a piece of text to the prompt.
        
        Args:
            text (str): The text to add
            name (str, optional): Name identifier for the text piece (unused in simple builder)
            text_role (str, optional): Role of the text (unused in simple builder)
        """
        self.text_pieces.append(SimplePromptTextPiece(text.strip(), name, text_role))

    def compile_prompt(self) -> str:
        """
        Compiles all added text pieces into a single prompt.
        
        Returns:
            str: The compiled prompt with empty lines between text pieces
        """
        if not self.text_pieces:
            return ""
        
        result = []
        for piece in self.text_pieces:
            tag_attrs = []
            if piece.name:
                tag_attrs.append(f'name="{piece.name}"')
            if piece.text_role:
                tag_attrs.append(f'role="{piece.text_role}"')
            
            if tag_attrs:
                tag_start = f'<text {" ".join(tag_attrs)}>'
            else:
                tag_start = '<text>'
                
            result.append(f'{tag_start}\n{piece.text}\n</text>')
            
        return '\n\n'.join(result)


class SimplePromptBuilderFactory(PromptBuilderFactory):
    def create_prompt_builder(self) -> PromptBuilder:
        return SimplePromptBuilder()
    
    def get_help_message(self) -> str:
        return textwrap.dedent("""
        The user prompts are wrapped in simple xml tags to help you understand the structure of the prompt. 
        This structure is applied only to the user prompts, not to the assistant responses. 
        Check other instructions for assistant response format.
        """)
