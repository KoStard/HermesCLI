from abc import ABC, abstractmethod
from typing import Optional

from hermes.file_processors.base import FileProcessor

class PromptBuilder(ABC):
    @abstractmethod
    def __init__(self, file_processor: FileProcessor, author: str, do_introduction: bool = False):
        pass

    @abstractmethod
    def add_text(self, text: str, name: Optional[str] = None):
        """
        Add a text piece to the prompt.
        
        :param text: The text to add
        :param name: Optional name for the text piece, allowing reference from another piece
        """
        pass

    @abstractmethod
    def add_file(self, file_path: str, name: str):
        """
        Add a file to the prompt.
        
        :param file_path: Path to the file to add
        :param name: Name for the file, allowing reference from another piece
        """
        pass

    @abstractmethod
    def add_image(self, image_path: str, name: str):
        """
        Add an image to the prompt.
        
        :param image_path: Path to the image file to add
        :param name: Name for the image, allowing reference from another piece
        """
        pass

    @abstractmethod
    def build_prompt(self):
        """
        Build and return the final prompt object.
        
        :return: The constructed prompt
        """
        pass

    @abstractmethod
    def erase(self):
        """
        Erase the entire prompt and give it a fresh start.
        """
        pass
