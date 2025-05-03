from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class KnowledgeEntry:
    """Represents a single entry in the shared knowledge base."""

    content: str
    author_node_title: str  # Title of the node that added the entry
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    title: str | None = None  # Optional short title/summary
    tags: list[str] = field(default_factory=list)  # Optional tags for categorization

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entry metadata to a dictionary for frontmatter."""
        data = {
            "timestamp": self.timestamp,
            "author_node_title": self.author_node_title,
        }
        if self.title:
            data["title"] = self.title
        if self.tags:
            data["tags"] = self.tags
        return data

    @staticmethod
    def from_dict(data: dict[str, Any], content: str) -> "KnowledgeEntry":
        """Deserialize metadata from a dictionary and combine with content."""
        return KnowledgeEntry(
            content=content,
            author_node_title=data.get("author_node_title", "Unknown"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            title=data.get("title"),
            tags=data.get("tags", []),
        )
