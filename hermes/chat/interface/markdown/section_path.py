from .header import Header


class SectionPath:
    """Manages the current path in a markdown document hierarchy."""

    def __init__(self):
        self.current_path: list[str] = []

    def update(self, header: Header) -> None:
        """
        Update the current path based on a new header.

        Args:
            header: The new header encountered
        """
        if header.level > len(self.current_path):
            self.current_path.append(header.title)
        else:
            self.current_path = self.current_path[: header.level - 1]
            self.current_path.append(header.title)

    def matches(self, target_path: list[str]) -> bool:
        """Check if current path matches target path."""
        return self.current_path == target_path

    def get_level(self) -> int:
        """Get current nesting level."""
        return len(self.current_path)
