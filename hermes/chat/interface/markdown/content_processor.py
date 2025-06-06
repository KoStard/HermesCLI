from .header import Header
from .section_finder import SectionFinder
from .section_path import SectionPath


class ContentProcessor:
    """Processes markdown content for section updates."""

    def __init__(self):
        self.section_finder = SectionFinder()

    def process_content(
        self, lines: list[str], section_path: list[str], new_content: str, mode: str, is_preface: bool = False
    ) -> tuple[list[str], bool]:
        """Process document lines and apply the update."""
        self._validate_mode(mode)
        actual_section_path = self._get_actual_section_path(section_path, is_preface)
        return self._process_lines(lines, actual_section_path, new_content, mode, is_preface)

    def _validate_mode(self, mode: str) -> None:
        """Validate the update mode."""
        if mode not in ["append_markdown_section", "update_markdown_section"]:
            raise ValueError(f"Invalid mode: {mode}")

    def _get_actual_section_path(self, section_path: list[str], is_preface: bool) -> list[str]:
        """Get the actual section path considering preface special case."""
        return section_path[:-1] if is_preface else section_path

    def _process_lines(
        self, lines: list[str], section_path: list[str], new_content: str, mode: str, is_preface: bool
    ) -> tuple[list[str], bool]:
        """Process lines and track section matches."""
        path_tracker = SectionPath()
        updated_lines = []
        i = 0
        section_found = False

        while i < len(lines):
            i = self._process_line(lines, i, path_tracker, section_path, new_content, mode, is_preface, updated_lines)
            if path_tracker.matches(section_path):
                section_found = True
            i += 1

        return updated_lines, section_found

    def _process_line(
        self,
        lines: list[str],
        i: int,
        path_tracker: SectionPath,
        section_path: list[str],
        new_content: str,
        mode: str,
        is_preface: bool,
        updated_lines: list[str],
    ) -> int:
        """Process a single line and update path tracker."""
        line = lines[i]
        header = Header.parse(line)

        if not header:
            updated_lines.append(line)
            return i

        path_tracker.update(header)
        if not path_tracker.matches(section_path):
            updated_lines.append(line)
            return i

        return self._handle_section_match(lines, i, header.level, new_content, mode, is_preface, updated_lines)

    def _handle_section_match(
        self, lines: list[str], i: int, level: int, new_content: str, mode: str, is_preface: bool, updated_lines: list[str]
    ) -> int:
        """Handle when a section match is found."""
        if is_preface:
            return self._handle_preface_update(lines, i, new_content, mode, updated_lines)
        elif mode == "append_markdown_section":
            return self._handle_append(lines, i, level, new_content, updated_lines)
        else:  # update_markdown_section
            return self._handle_update(lines, i, level, new_content, updated_lines)

    def _handle_preface_update(self, lines: list[str], i: int, new_content: str, mode: str, updated_lines: list[str]) -> int:
        """Handle updating the preface of a section."""
        line = lines[i]
        next_section_idx = self._find_next_section_index(lines, i)

        if mode == "append_markdown_section":
            self._append_preface_content(lines, i, next_section_idx, new_content, updated_lines)
        else:  # update_markdown_section
            self._update_preface_content(line, new_content, updated_lines)

        return next_section_idx - 1

    def _find_next_section_index(self, lines: list[str], i: int) -> int:
        """Find index of the next section after position i."""
        start_of_next = self.section_finder.find_start_of_next_section(lines[i + 1 :]) + 1
        return i + start_of_next

    def _append_preface_content(self, lines: list[str], i: int, next_idx: int, new_content: str, updated_lines: list[str]) -> None:
        """Append content to preface section."""
        updated_lines.extend(lines[i:next_idx])
        updated_lines.append(new_content)

    def _update_preface_content(self, line: str, new_content: str, updated_lines: list[str]) -> None:
        """Update preface content."""
        updated_lines.extend([line, new_content])

    def _handle_append(self, lines: list[str], i: int, level: int, new_content: str, updated_lines: list[str]) -> int:
        """Handle appending content to a section."""
        section_end = self._find_section_end(lines, i, level)
        updated_lines.extend(lines[i:section_end])
        updated_lines.append(new_content)
        return section_end - 1

    def _find_section_end(self, lines: list[str], i: int, level: int) -> int:
        """Find the end index of a section."""
        section_end = self.section_finder.find_section_end(lines[i + 1 :], level) + 1
        return i + section_end

    def _handle_update(self, lines: list[str], i: int, level: int, new_content: str, updated_lines: list[str]) -> int:
        """Handle updating a section's content."""
        updated_lines.append(lines[i])  # Add the header
        updated_lines.append(new_content)
        return self._find_next_header_index(lines, i, level) - 1

    def _find_next_header_index(self, lines: list[str], i: int, level: int) -> int:
        """Find index of the next header at same or higher level."""
        j = i + 1
        while j < len(lines):
            header = Header.parse(lines[j])
            if header and header.level <= level:
                return j
            j += 1
        return j
