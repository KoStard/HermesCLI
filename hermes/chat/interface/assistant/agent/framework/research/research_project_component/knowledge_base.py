from dataclasses import dataclass
import dataclasses
from datetime import datetime
from pathlib import Path
from typing import Any

from hermes.chat.interface.assistant.agent.framework.research.file_system import FileSystem
from hermes.chat.interface.assistant.agent.framework.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)


class KnowledgeEntry:
    """Represents a single entry in the shared knowledge base."""

    def __init__(
        self,
        title: str,
        content: str,
        author_node_title: str,
        timestamp: datetime | None = None,
        tags: list[str] | None = None,
        source: str | None = None,
        importance: int = 1,
        confidence: int = 1,
    ):
        self.title = title
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.author_node_title = author_node_title
        self.tags = tags or []
        self.source = source
        self.importance = importance
        self.confidence = confidence

    def get_metadata_dict(self) -> dict[str, Any]:
        """Convert entry to a dictionary for serialization."""
        return {
            "title": self.title,
            "timestamp": self.timestamp.isoformat(),
            "author_node_title": self.author_node_title,
            "tags": self.tags,
            "source": self.source,
            "importance": self.importance,
            "confidence": self.confidence,
        }

    @staticmethod
    def from_dict(data: dict[str, Any], content: str) -> "KnowledgeEntry":
        """Create a KnowledgeEntry from a dictionary and content."""
        return KnowledgeEntry(
            title=data.get("title", "Untitled Entry"),
            content=content,
            author_node_title=data.get("author_node_title", "unknown author"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            tags=data.get("tags", []),
            source=data.get("source"),
            importance=data.get("importance", 1),
            confidence=data.get("confidence", 1),
        )


class KnowledgeBase:
    """Manages the knowledge base entries for a research project using individual files."""

    def __init__(self, file_system: FileSystem, repo_root_path: Path):
        self._file_system = file_system
        self._repo_root_path = repo_root_path
        self._knowledge_base_dir = repo_root_path / "Knowledgebase"
        self._entries: dict[str, KnowledgeEntry] = {}  # Map title to entry

    def load_entries(self) -> None:
        """Load knowledge base entries from individual files in /Knowledgebase/ folder."""
        if not self._file_system.directory_exists(self._knowledge_base_dir):
            return

        try:
            # Get all markdown files in the Knowledgebase directory
            for file_path in self._knowledge_base_dir.iterdir():
                if file_path.suffix == ".md":
                    try:
                        # Load the file using MarkdownFileWithMetadata
                        file_with_metadata = MarkdownFileWithMetadataImpl.load_from_file(file_path)
                        metadata = file_with_metadata.get_metadata()
                        content = file_with_metadata.get_content()

                        # Create KnowledgeEntry from the loaded data
                        entry = KnowledgeEntry.from_dict(metadata, content)
                        self._entries[entry.title] = entry
                    except Exception as e:
                        print(f"Warning: Error loading knowledge entry from {file_path}: {e}")
        except Exception as e:
            print(f"Error loading knowledge base directory: {e}")

    def save_entries(self) -> None:
        """Save knowledge base entries as individual files."""
        # Create the Knowledgebase directory if it doesn't exist
        if not self._file_system.directory_exists(self._knowledge_base_dir):
            self._file_system.create_directory(self._knowledge_base_dir)

        try:
            for entry in self._entries.values():
                self._save_entry(entry)
        except Exception as e:
            print(f"Error saving knowledge base: {e}")

    def _save_entry(self, entry: KnowledgeEntry) -> None:
        """Save a single knowledge entry to its individual file."""
        # Create a markdown file with metadata
        file_with_metadata = MarkdownFileWithMetadataImpl(entry.title, entry.content)

        # Set all metadata
        metadata = entry.get_metadata_dict()
        for key, value in metadata.items():
            file_with_metadata.set_metadata_key(key, value)

        # Save the file
        file_with_metadata.save_file(self._knowledge_base_dir)

    def add_entry(self, entry: KnowledgeEntry) -> None:
        """Add a new entry to the knowledge base and save."""
        # Check if title already exists (titles must be unique)
        if entry.title in self._entries:
            raise ValueError(f"Knowledge entry with title '{entry.title}' already exists")

        self._entries[entry.title] = entry
        self._save_entry(entry)

    def get_entry_by_title(self, title: str) -> KnowledgeEntry | None:
        """Get a knowledge entry by its title."""
        return self._entries.get(title)

    def append_content(self, title: str, append_content: str) -> bool:
        if title not in self._entries:
            return False

        entry = self._entries[title]
        entry.content += "\n\n" + append_content
        entry.timestamp = datetime.now()
        self._save_entry(entry)
        return True

    def update_entry(
        self, title: str, new_content: str, new_title: str | None = None
    ) -> bool:
        """Update an existing knowledge entry."""
        if title not in self._entries:
            return False

        entry = self._entries[title]

        self.delete_entry(title)

        entry.content = new_content
        if new_title:
            entry.title = new_title
        # Update timestamp
        entry.timestamp = datetime.now()
        self.add_entry(entry)
        return True

    def delete_entry(self, title: str) -> bool:
        """Delete a knowledge entry by its title."""
        if title not in self._entries:
            return False

        entry = self._entries[title]

        # Delete the file
        try:
            file_path = self._knowledge_base_dir / MarkdownFileWithMetadataImpl._get_sanitizen_filename(entry.title)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Warning: Error deleting knowledge entry file: {e}")

        # Remove from memory
        del self._entries[title]
        return True

    def get_entries(self) -> list[KnowledgeEntry]:
        """Get all knowledge base entries."""
        return list(self._entries.values())

    def list_titles(self) -> list[str]:
        """Get a list of all entry titles."""
        return list(self._entries.keys())
