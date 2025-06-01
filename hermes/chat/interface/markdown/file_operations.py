import os
import shutil
from datetime import datetime


class FileOperations:
    """Handles file system operations for markdown documents."""

    def __init__(self, backup_dir: str = "/tmp/hermes/backups"):
        self.backup_dir = backup_dir

    def read_file(self, file_path: str) -> list[str]:
        """Read a file and return its contents as a list of lines."""
        with open(file_path, encoding="utf-8") as f:
            return f.readlines()

    def write_file(self, file_path: str, lines: list[str]) -> None:
        """Write lines to a file."""
        self._ensure_directory_exists(file_path)
        self._write_lines_to_file(file_path, lines)

    def _ensure_directory_exists(self, file_path: str) -> None:
        """Ensure the directory for a file exists."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def _write_lines_to_file(self, file_path: str, lines: list[str]) -> None:
        """Write lines to a file."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def create_new_file(self, file_path: str, section_path: list[str], content: str) -> None:
        """Create a new markdown file with initial section structure."""
        self._ensure_directory_exists(file_path)
        lines = self._generate_file_content(section_path, content)
        self._write_lines_to_file(file_path, lines)

    def _generate_file_content(self, section_path: list[str], content: str) -> list[str]:
        """Generate content for a new file with headers."""
        lines = []
        for i, header in enumerate(section_path, 1):
            lines.append(f"{'#' * i} {header}\n")
        lines.append(content)
        return lines

    def backup_file(self, file_path: str) -> None:
        """Create a backup copy of the file."""
        if not self.file_exists(file_path):
            return

        self._ensure_backup_dir_exists()
        backup_path = self._generate_backup_path(file_path)
        shutil.copy2(file_path, backup_path)

    def _ensure_backup_dir_exists(self) -> None:
        """Ensure backup directory exists."""
        os.makedirs(self.backup_dir, exist_ok=True)

    def _generate_backup_path(self, file_path: str) -> str:
        """Generate a backup file path with timestamp."""
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.backup_dir, f"{filename}_{timestamp}.bak")

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        return os.path.exists(file_path)
