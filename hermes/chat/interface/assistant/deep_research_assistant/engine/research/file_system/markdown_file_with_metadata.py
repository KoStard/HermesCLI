from abc import ABC, abstractmethod
from typing import Any


class MarkdownFileWithMetadata(ABC):
    @abstractmethod
    def add_property(self, name: str, value: Any):
        pass

    @abstractmethod
    def add_user_friendly_name(self, user_friendly_name):
        """
        Each file has a filename.
        But for markdown files with metadata, we can store the user-friendly name as a property, while save it in a filesystem-friendly filename file.
        We are given with user_friendly_name and we'll build the raw filename. user_friendly_name won't have a file extension either.
        """
        pass

    @abstractmethod
    def get_filename(self) -> str:
        pass

    @abstractmethod
    def get_user_friendly_name(self) -> str:
        pass


class MarkdownFileWithMetadataImpl(MarkdownFileWithMetadata):
    pass
