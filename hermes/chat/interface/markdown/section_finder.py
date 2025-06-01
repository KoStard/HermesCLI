from .header import Header
from .section_path import SectionPath


class SectionFinder:
    """Finds sections in markdown documents."""

    def find_section_end(self, lines: list[str], current_level: int) -> int:
        """Find the end index of current section."""
        return self._find_header_with_level(lines, current_level)

    def _find_header_with_level(self, lines: list[str], max_level: int) -> int:
        """Find index of first header with level <= max_level."""
        for i, line in enumerate(lines):
            if self._is_header_with_max_level(line, max_level):
                return i
        return len(lines)

    def _is_header_with_max_level(self, line: str, max_level: int) -> bool:
        """Check if line is a header with level <= max_level."""
        header = Header.parse(line)
        return header is not None and header.level <= max_level

    def find_start_of_next_section(self, lines: list[str]) -> int:
        """Find the start index of the next section."""
        return self._find_any_header(lines)

    def _find_any_header(self, lines: list[str]) -> int:
        """Find index of first header in lines."""
        for i, line in enumerate(lines):
            if Header.parse(line):
                return i
        return len(lines)

    def find_section(self, lines: list[str], section_path: list[str]) -> tuple[int, int, bool]:
        """Find a section in the document."""
        path_tracker = SectionPath()

        for i, line in enumerate(lines):
            if not self._update_path_and_check_match(path_tracker, line, section_path):
                continue

            return self._get_section_bounds(i, lines, Header.parse(line).level)

        return -1, -1, False

    def _update_path_and_check_match(
        self, path_tracker: SectionPath, line: str, section_path: list[str]
    ) -> bool:
        """Update path tracker with line and check if it matches section_path."""
        header = Header.parse(line)
        if not header:
            return False

        path_tracker.update(header)
        return path_tracker.matches(section_path)

    def _get_section_bounds(
        self, start_idx: int, lines: list[str], level: int
    ) -> tuple[int, int, bool]:
        """Get section bounds given start index and header level."""
        end_idx = start_idx + 1 + self.find_section_end(lines[start_idx + 1:], level)
        return start_idx, end_idx, True
