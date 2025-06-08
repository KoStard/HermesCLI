from .header import Header


class SectionPath:
    """Manages the current path in a markdown document hierarchy."""

    def __init__(self):
        self.current_path: list[str] = []
        self.min_level: int = 1  # Track the minimum header level seen

    def update(self, header: Header) -> None:
        """Update the current path based on a new header.

        Args:
            header: The new header encountered
        """
        # Update minimum level seen if this is the first header or lower than current min
        if not self.current_path or header.level < self.min_level:
            self.min_level = header.level

        # Calculate relative level (adjusted for non-H1 starts)
        relative_level = header.level - self.min_level + 1

        if relative_level > len(self.current_path):
            self.current_path.append(header.title)
        else:
            self.current_path = self.current_path[: relative_level - 1]
            self.current_path.append(header.title)

    def matches(self, target_path: list[str]) -> bool:
        """Check if current path matches target path."""
        return self.current_path == target_path

    def get_level(self) -> int:
        """Get current nesting level."""
        return len(self.current_path)

    def get_min_level(self) -> int:
        """Get minimum header level seen."""
        return self.min_level
