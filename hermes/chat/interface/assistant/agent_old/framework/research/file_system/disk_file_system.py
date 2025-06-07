import os
import shutil
from pathlib import Path

from .. import file_system


class DiskFileSystem(file_system.FileSystem):
    """Implementation of FileSystem interface that works with the local disk file system."""

    def read_file(self, path: Path) -> str:
        """Read content from a file at the given path.

        Args:
            path: Path to the file to read

        Returns:
            The content of the file as a string

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        with open(path, encoding="utf-8") as f:
            return f.read()

    def write_file(self, path: Path, content: str, auto_create_directories: bool = True) -> None:
        """Write content to a file at the given path.

        Args:
            path: Path to the file to write
            content: Content to write to the file
            auto_create_directories: If True, create parent directories if they don't exist

        Raises:
            IOError: If writing fails
        """
        if auto_create_directories:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def copy_file(self, origin_path: Path, destination_path: Path) -> None:
        """Copy a file from origin to destination.

        Args:
            origin_path: Path to the source file
            destination_path: Path where the file should be copied

        Raises:
            FileNotFoundError: If the source file doesn't exist
            IOError: If copying fails
        """
        # Make sure destination directory exists
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin_path, destination_path)

    def directory_exists(self, path: Path) -> bool:
        """Check if a directory exists at the given path.

        Args:
            path: Path to check

        Returns:
            True if the directory exists, False otherwise
        """
        return path.exists() and path.is_dir()

    def file_exists(self, path: Path) -> bool:
        """Check if a file exists at the given path.

        Args:
            path: Path to check

        Returns:
            True if the file exists, False otherwise
        """
        return path.exists() and path.is_file()

    def create_directory(self, path: Path) -> None:
        """Create a directory at the given path.

        Args:
            path: Path where to create the directory

        Raises:
            IOError: If creating the directory fails
        """
        path.mkdir(parents=True, exist_ok=True)

    def list_files(self, directory: Path, pattern: str | None = None) -> list[Path]:
        """List files in a directory, optionally filtered by a pattern.

        Args:
            directory: Directory to list files from
            pattern: Optional glob pattern to filter files

        Returns:
            List of paths to files in the directory
        """
        if pattern:
            return list(directory.glob(pattern))
        return [p for p in directory.iterdir() if p.is_file()]

    def is_empty(self, directory: Path) -> bool:
        return not any(os.scandir(directory))
