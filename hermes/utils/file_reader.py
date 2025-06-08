import logging
import os

from hermes.utils.binary_file import is_binary

logger = logging.getLogger(__name__)


class FileReader:
    """Utility class for reading files with appropriate format handling and fallback strategies.
    Supports Jupyter notebooks, markdown files, and plain text files.
    """

    @staticmethod
    def read_file(filepath: str) -> tuple[str, bool]:
        """Read a file with appropriate format handling.

        Args:
            filepath: Path to the file to read

        Returns:
            Tuple[str, bool]: (file content, success flag)
        """
        if not os.path.exists(filepath):
            return FileReader._handle_nonexistent_file(filepath)

        # Special handling for Jupyter notebooks
        if filepath.endswith(".ipynb"):
            result = FileReader._read_jupyter_notebook(filepath)
            if result[1]:  # If successful
                return result

        # Try using markitdown first
        result = FileReader._read_with_markitdown(filepath)
        if result[1]:  # If successful
            return result

        # Fall back to plain text or binary handling
        return FileReader._read_as_plain_text(filepath)

    @staticmethod
    def _handle_nonexistent_file(filepath: str) -> tuple[str, bool]:
        """Handle case where file doesn't exist."""
        logger.error(f"File does not exist: {filepath}")
        return f"Error: File does not exist: {filepath}", False

    @staticmethod
    def _read_jupyter_notebook(filepath: str) -> tuple[str, bool]:
        """Read a Jupyter notebook file using custom converter."""
        try:
            from hermes.chat.interface.assistant.models.request_builder.notebook_converter import (
                convert_notebook_custom,
            )

            content = convert_notebook_custom(filepath)
            return content, True
        except Exception as e:
            logger.error(f"Error converting notebook {filepath}: {e}")
            return "", False

    @staticmethod
    def _read_with_markitdown(filepath: str) -> tuple[str, bool]:
        """Try to read file using markitdown library."""
        try:
            from markitdown import MarkItDown

            markitdown = MarkItDown()
            conversion_result = markitdown.convert(filepath)
            return conversion_result.text_content, True
        except Exception as e:
            logger.debug(f"Failed to use markitdown for {filepath}, reading as text file: {e}")
            return "", False

    @staticmethod
    def _read_as_plain_text(filepath: str) -> tuple[str, bool]:
        """Read as plain text if possible, handle binary files."""
        if not is_binary(filepath):
            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                return content, True
            except Exception as read_error:
                logger.error(f"Failed to read text file {filepath}: {read_error}")
                return f"Error reading file {filepath}: {read_error}", False
        else:
            logger.error(f"Cannot read binary file {filepath}")
            return f"Error: Cannot read binary file {filepath}", False

    @staticmethod
    def _process_single_file(full_path: str, directory_path: str, result: dict) -> None:
        """Process a single file and add its content to the result dictionary if successfully read.

        Args:
            full_path: Full path to the file
            directory_path: Base directory path for calculating relative paths
            result: Dictionary to update with file content
        """
        # Get the file name without the path
        file_name = os.path.basename(full_path)

        # Skip hidden files
        if file_name.startswith("."):
            return

        relative_path = os.path.relpath(full_path, directory_path)
        content, success = FileReader.read_file(full_path)
        if success:
            result[relative_path] = content

    @staticmethod
    def read_directory(directory_path: str) -> dict:
        """Read all files in a directory recursively.

        Args:
            directory_path: Path to the directory

        Returns:
            dict: Dictionary mapping relative file paths to content
        """
        result = {}

        if not os.path.isdir(directory_path):
            logger.error(f"Not a directory: {directory_path}")
            return result

        for root, _, files in os.walk(directory_path):
            for file in files:
                full_path = os.path.join(root, file)
                FileReader._process_single_file(full_path, directory_path, result)

        return result
