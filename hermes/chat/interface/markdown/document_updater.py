from .content_processor import ContentProcessor
from .file_operations import FileOperations


class MarkdownDocumentUpdater:
    """Orchestrates operations for updating markdown document sections."""

    def __init__(self, file_path: str, backup_dir: str = "/tmp/hermes/backups"):
        self.file_path = file_path
        self.file_ops = FileOperations(backup_dir)
        self.content_processor = ContentProcessor()

    def update_section(self, section_path: list[str], new_content: str, mode: str) -> bool:
        """Update a section in the markdown document."""
        content = self._ensure_newline(new_content)

        if not self._file_exists():
            return self._create_new_file(section_path, content)

        return self._update_existing_file(section_path, content, mode)

    def _ensure_newline(self, content: str) -> str:
        """Ensure content ends with a newline."""
        return content if content.endswith("\n") else content + "\n"

    def _file_exists(self) -> bool:
        """Check if the target file exists."""
        return self.file_ops.file_exists(self.file_path)

    def _create_new_file(self, section_path: list[str], content: str) -> bool:
        """Create a new file with the given content."""
        self.file_ops.create_new_file(self.file_path, section_path, content)
        return True

    def _update_existing_file(
        self, section_path: list[str], content: str, mode: str
    ) -> bool:
        """Update an existing file."""
        self.file_ops.backup_file(self.file_path)
        lines = self.file_ops.read_file(self.file_path)

        path, is_preface = self._process_section_path(section_path)
        updated_lines, found = self._process_content(lines, path, content, mode, is_preface)

        self.file_ops.write_file(self.file_path, updated_lines)
        return found

    def _process_section_path(self, section_path: list[str]) -> tuple[list[str], bool]:
        """Process section path and check for preface special case."""
        is_preface = False
        path = section_path

        if len(section_path) > 0 and section_path[-1] == "__preface":
            is_preface = True
            path = section_path[:-1]

        return path, is_preface

    def _process_content(
        self, lines: list[str], path: list[str], content: str, mode: str, is_preface: bool
    ) -> tuple[list[str], bool]:
        """Process content using the content processor."""
        return self.content_processor.process_content(
            lines, path, content, mode, is_preface
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Markdown Document Updater")
    parser.add_argument("file_path", type=str, help="Path to the markdown file")
    args = parser.parse_args()
    updater = MarkdownDocumentUpdater(args.file_path)
    updater.update_section(["T1"], "New content for Section 1.1", "update_markdown_section")
