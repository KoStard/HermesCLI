from datetime import datetime
from pathlib import Path
from typing import Any

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system import FileSystem
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.markdown_file_with_metadata import MarkdownFileWithMetadataImpl


class KnowledgeEntry:
    """Represents a single entry in the shared knowledge base."""

    def __init__(
        self,
        title: str,
        content: str,
        timestamp: datetime = None,
        tags: list[str] = None,
        source: str | None = None,
        importance: int = 1,
        confidence: int = 1
    ):
        self.title = title
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.tags = tags or []
        self.source = source
        self.importance = importance
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        """Convert entry to a dictionary for serialization."""
        return {
            "title": self.title,
            "timestamp": self.timestamp.isoformat(),
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
        self._knowledge_separator = "\n\n<!-- HERMES_KNOWLEDGE_ENTRY_SEPARATOR -->\n\n"

    def load_entries(self) -> None:
        """Load knowledge base entries from file."""
        if not self._file_system.file_exists(self._knowledge_base_path):
            return

        try:
            content = self._file_system.read_file(self._knowledge_base_path)
            entry_blocks = content.split(self._knowledge_separator)

            for block in entry_blocks:
                block = block.strip()
                if not block:
                    continue
                try:
                    # Create a temporary file-like object to use with MarkdownFileWithMetadataImpl
                    from io import StringIO
                    temp_file = StringIO(block)
                    
                    # Use the load_from_string method (we need to add this method)
                    md_file = self._load_markdown_from_string(block)
                    
                    metadata = md_file.get_metadata()
                    content = md_file.get_content()
                    
                    if metadata:
                        entry = KnowledgeEntry.from_dict(metadata, content)
                        self._entries.append(entry)
                except Exception as e:
                    print(f"Warning: Error parsing knowledge entry: {e}")
        except Exception as e:
            print(f"Error loading knowledge base: {e}")

    def save_entries(self) -> None:
        """Save knowledge base entries to file."""
        try:
            entry_strings = []
            # Sort by timestamp before saving
            sorted_entries = sorted(self._entries, key=lambda x: x.timestamp)

            for entry in sorted_entries:
                md_file = MarkdownFileWithMetadataImpl()
                md_file.set_content(entry.content)
                
                # Add all metadata properties
                for key, value in entry.to_dict().items():
                    md_file.set_metadata_key(key, value)
                
                # Get the content with frontmatter
                with StringIO() as string_buffer:
                    md_file.save_file_to_string(string_buffer)
                    entry_string = string_buffer.getvalue()
                
                entry_strings.append(entry_string)

            full_content = self._knowledge_separator.join(entry_strings)
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
    def _load_markdown_from_string(self, content: str) -> MarkdownFileWithMetadataImpl:
        """Helper method to load a MarkdownFileWithMetadataImpl from a string."""
        from io import StringIO
        
        # Create a simple markdown file instance
        md_file = MarkdownFileWithMetadataImpl()
        
        # Use the FrontmatterManager directly since we're just parsing
        from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.frontmatter_manager import FrontmatterManager
        frontmatter_manager = FrontmatterManager()
        metadata, parsed_content = frontmatter_manager.extract_frontmatter(content)
        
        md_file.set_content(parsed_content)
        for key, value in metadata.items():
            md_file.set_metadata_key(key, value)
        
        return md_file
