from datetime import datetime
from pathlib import Path
from typing import Any

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system import FileSystem
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.frontmatter_manager import (
    FrontmatterManager,
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
        confidence: int = 1
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
    """Manages the knowledge base entries for a research project."""

    def __init__(self, file_system: FileSystem, knowledge_base_path: Path):
        self._file_system = file_system
        self._knowledge_base_path = knowledge_base_path
        self._entries: list[KnowledgeEntry] = []
        # Define a unique separator for knowledge base entries in the Markdown file
        self._knowledge_separator = "\n<!-- HERMES_KNOWLEDGE_ENTRY_SEPARATOR -->\n"

    def load_entries(self) -> None:
        """Load knowledge base entries from file."""
        if not self._file_system.file_exists(self._knowledge_base_path):
            return

        frontmatter_manager = FrontmatterManager()

        try:
            content = self._file_system.read_file(self._knowledge_base_path)
            entry_blocks = content.split(self._knowledge_separator)

            for block in entry_blocks:
                block = block.strip()
                if not block:
                    continue
                try:
                    metadata, content = frontmatter_manager.extract_frontmatter(content)
                    entry = KnowledgeEntry.from_dict(metadata, content)
                    self._entries.append(entry)
                except Exception as e:
                    print(f"Warning: Error parsing knowledge entry: {e}")
        except Exception as e:
            print(f"Error loading knowledge base: {e}")

    def save_entries(self) -> None:
        """Save knowledge base entries to file."""
        frontmatter_manager = FrontmatterManager()
        try:
            entry_strings = []
            # Sort by timestamp before saving
            sorted_entries = sorted(self._entries, key=lambda x: x.timestamp)

            for entry in sorted_entries:
                entry_string = frontmatter_manager.add_frontmatter(entry.content, entry.get_metadata_dict())
                entry_strings.append(entry_string)

            full_content = ("\n" + self._knowledge_separator + "\n").join(entry_strings)
            self._file_system.write_file(self._knowledge_base_path, full_content, True)
        except Exception as e:
            print(f"Error saving knowledge base: {e}")

    def add_entry(self, entry: KnowledgeEntry) -> None:
        """Add a new entry to the knowledge base and save."""
        self._entries.append(entry)
        self.save_entries()

    def get_entries(self) -> list[KnowledgeEntry]:
        """Get all knowledge base entries."""
        return self._entries.copy()
