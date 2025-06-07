from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from hermes.chat.interface.assistant.deep_research.research.file_system.filename import MarkdownFilename
from hermes.chat.interface.assistant.deep_research.research.file_system.frontmatter_manager import FrontmatterManager


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
    def save_file_in_directory(self, directory_path: Path) -> Path:
        pass

    @abstractmethod
    def set_content(self, content: str):
        pass

    @abstractmethod
    def get_content(self) -> str:
        pass

    @staticmethod
    @abstractmethod
    def load_from_file(filepath: Path) -> "FileWithMetadata":
        pass

    @staticmethod
    @abstractmethod
    def load_from_directory(directory_path: Path, user_friendly_name: str) -> "FileWithMetadata":
        """Load a file with metadata from a directory using its user-friendly name"""
        pass

    @staticmethod
    @abstractmethod
    def file_exists(directory_path: Path, user_friendly_name: str) -> bool:
        """Check if a file with the given user-friendly name exists in the directory"""
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
        self.set_metadata_key("name", user_friendly_name)
        self._filename = self._get_sanitizen_filename(user_friendly_name)

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

    def save_file_in_directory(self, directory_path: Path) -> Path:
        """Save the markdown file with metadata as frontmatter."""
        full_content = self._frontmatter_manager.add_frontmatter(self._content, self.metadata)
        assert self._filename is not None
        path = directory_path / self._filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(full_content)
        return path

    def save_file_in_path(self, filepath: Path):
        full_content = self._frontmatter_manager.add_frontmatter(self._content, self.metadata)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)

    def get_path(self, directory_path: Path) -> Path:
        assert self._filename is not None
        return directory_path / self._filename

    @staticmethod
    def _get_sanitizen_filename(user_friendly_name: str) -> str:
        """Convert a user-friendly name to a filesystem-safe filename."""
        filename_handler = MarkdownFilename(user_friendly_name)
        return filename_handler.get_os_aware_path()

    @staticmethod
    def load_from_directory(directory_path: Path, user_friendly_name: str) -> "FileWithMetadata":
        """Load a markdown file with frontmatter using its user-friendly name."""
        filename = MarkdownFileWithMetadataImpl._get_sanitizen_filename(user_friendly_name)
        filepath = directory_path / filename

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, encoding="utf-8") as f:
            file_content = f.read()

        frontmatter_manager = FrontmatterManager()
        metadata, content = frontmatter_manager.extract_frontmatter(file_content)

        # Use the provided user-friendly name
        md_file = MarkdownFileWithMetadataImpl(user_friendly_name, content)
        md_file.metadata = metadata

        return md_file

    @staticmethod
    def file_exists(directory_path: Path, user_friendly_name: str) -> bool:
        """Check if a file with the given user-friendly name exists in the directory."""
        filename = MarkdownFileWithMetadataImpl._get_sanitizen_filename(user_friendly_name)
        filepath = directory_path / filename
        return filepath.exists()

    @staticmethod
    def load_from_file(filepath: Path) -> "FileWithMetadata":
        """Load a markdown file with frontmatter."""
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, encoding="utf-8") as f:
            file_content = f.read()

        frontmatter_manager = FrontmatterManager()
        metadata, content = frontmatter_manager.extract_frontmatter(file_content)

        # Use the provided user-friendly name
        md_file = MarkdownFileWithMetadataImpl(metadata.get("name", filepath.stem), content)
        md_file.metadata = metadata

        return md_file
