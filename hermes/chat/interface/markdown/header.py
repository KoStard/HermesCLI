from dataclasses import dataclass
from typing import Optional


@dataclass
class Header:
    """Represents a markdown header with level and title."""

    raw_line: str
    level: int
    title: str

    @staticmethod
    def parse(line: str) -> Optional["Header"]:
        """
        Parse a line and return a Header object if it's a markdown header.

        Args:
            line: A line from the document

        Returns:
            Header object if line is a header, None otherwise
        """
        if line.startswith("#"):
            stripped = line.lstrip("#")
            level = len(line) - len(stripped)
            title = stripped.strip()
            return Header(raw_line=line, level=level, title=title)
        return None
