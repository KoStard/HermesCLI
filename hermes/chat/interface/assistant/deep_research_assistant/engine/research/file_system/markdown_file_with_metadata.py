from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.filename import Filename
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.frontmatter_manager import FrontmatterManager


class FileWithMetadata(ABC):
    @abstractmethod
    def add_property(self, name: str, value: Any):
        pass

    @abstractmethod
    def add_user_friendly_name(self, user_friendly_name):
        """
        Each file has a filename.
        But for markdown files with metadata, we can store the user-friendly name as a property, while save it in a filesystem-friendly
        filename file.
        We are given with user_friendly_name and we'll build the raw filename. user_friendly_name won't have a file extension either.
        """
        pass

    @abstractmethod
    def get_filename(self) -> str:
        pass

    @abstractmethod
    def get_user_friendly_name(self) -> str:
        pass

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def set_metadata_key(self, key: str, value: Any):
        pass

    @abstractmethod
    def delete_metadata_key(self, key: str):
        pass

    @abstractmethod
    def save_file(self, directory_path: Path) -> Path:
        pass

    @abstractmethod
    def set_content(self, content: str):
        pass

    @abstractmethod
    def get_content(self) -> str:
        pass

    @staticmethod
    @abstractmethod
    def load_from_file(filepath: str) -> 'FileWithMetadata':
        pass


class MarkdownFileWithMetadataImpl(FileWithMetadata):
    """Implementation of MarkdownFileWithMetadata."""

    def __init__(self, user_friendly_name: str | None = None, content: str = ""):
        self.metadata: dict[str, Any] = {}
        self._filename = None
        self._user_friendly_name = None
        self._content = content
        self._frontmatter_manager = FrontmatterManager()
        if user_friendly_name:
            self.add_user_friendly_name(user_friendly_name)

    def add_property(self, name: str, value: Any):
        """Add or update a property in the metadata."""
        self.metadata[name] = value

    def add_user_friendly_name(self, user_friendly_name):
        """Set the user-friendly name and generate a filesystem-friendly filename."""
        self._user_friendly_name = user_friendly_name
        filename_handler = Filename(user_friendly_name)
        self._filename = filename_handler.get_os_aware_path()

    def get_filename(self) -> str:
        """Get the filesystem-friendly filename."""
        assert self._filename is not None
        return self._filename

    def get_user_friendly_name(self) -> str:
        """Get the user-friendly name."""
        assert self._user_friendly_name is not None
        return self._user_friendly_name

    def get_metadata(self) -> dict[str, Any]:
        """Get the metadata dictionary."""
        return self.metadata.copy() if self.metadata else {}

    def set_metadata_key(self, key: str, value: Any):
        """Set a specific metadata key."""
        self.metadata[key] = value

    def delete_metadata_key(self, key: str):
        """Delete a specific metadata key if it exists."""
        if key in self.metadata:
            del self.metadata[key]

    def set_content(self, content: str):
        """Set the content of the markdown file."""
        self._content = content

    def get_content(self) -> str:
        """Get the content of the markdown file."""
        return self._content

    def save_file(self, directory_path: Path) -> Path:
        """Save the markdown file with metadata as frontmatter."""
        full_content = self._frontmatter_manager.add_frontmatter(self._content, self.metadata)
        assert self._filename is not None
        path = directory_path / self._filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(full_content)

    @staticmethod
    def load_from_file(filepath: str) -> 'FileWithMetadata':
        """Load a markdown file with frontmatter."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, encoding='utf-8') as f:
            file_content = f.read()

        frontmatter_manager = FrontmatterManager()
        metadata, content = frontmatter_manager.extract_frontmatter(file_content)

        # Extract filename without extension for user-friendly name
        filename = path.stem

        md_file = MarkdownFileWithMetadataImpl(filename, content)
        md_file.metadata = metadata

        return md_file
