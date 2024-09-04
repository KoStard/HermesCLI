from abc import ABC, abstractmethod
from typing import Optional

class PromptBuilder(ABC):
    @abstractmethod
    def add_text(self, text: str, name: Optional[str] = None):
        """
        Add a text piece to the prompt.
        
        :param text: The text to add
        :param name: Optional name for the text piece, allowing reference from another piece
        """
        pass

    @abstractmethod
    def add_file(self, file_path: str, name: Optional[str] = None):
        """
        Add a file to the prompt.
        
        :param file_path: Path to the file to add
        :param name: Optional name for the file, allowing reference from another piece
        """
        pass

    @abstractmethod
    def add_image(self, image_path: str, name: Optional[str] = None):
        """
        Add an image to the prompt.
        
        :param image_path: Path to the image file to add
        :param name: Optional name for the image, allowing reference from another piece
        """
        pass

    @abstractmethod
    def build_prompt(self) -> str:
        """
        Build and return the final prompt string.
        
        :return: The constructed prompt as a string
        """
        pass
