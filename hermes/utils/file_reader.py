import logging
import os

from hermes.utils.binary_file import is_binary

logger = logging.getLogger(__name__)


class FileReader:
    """
    Utility class for reading files with appropriate format handling and fallback strategies.
    Supports Jupyter notebooks, markdown files, and plain text files.
    """

    @staticmethod
    def read_file(filepath: str) -> tuple[str, bool]:
        """
        Read a file with appropriate format handling.

        Args:
            filepath: Path to the file to read

        Returns:
            Tuple[str, bool]: (file content, success flag)
        """
        if not os.path.exists(filepath):
            logger.error(f"File does not exist: {filepath}")
            return f"Error: File does not exist: {filepath}", False

        # Special handling for Jupyter notebooks
        if filepath.endswith(".ipynb"):
            try:
                from hermes.chat.interface.assistant.models.request_builder.notebook_converter import (
                    convert_notebook_custom,
                )

                content = convert_notebook_custom(filepath)
                return content, True
            except Exception as e:
                logger.error(f"Error converting notebook {filepath}: {e}")
                # Fall back to regular file handling

        # Try using markitdown
        try:
            from markitdown import MarkItDown

            markitdown = MarkItDown()
            conversion_result = markitdown.convert(filepath)
            return conversion_result.text_content, True
        except Exception as e:
            # Fall back to plain text for non-binary files
            if not is_binary(filepath):
                logger.debug(f"Failed to use markitdown for {filepath}, reading as text file: {e}")
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
    def read_directory(directory_path: str) -> dict:
        """
        Read all files in a directory recursively.

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
                # Skip hidden files
                if file.startswith("."):
                    continue

                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, directory_path)

                content, success = FileReader.read_file(full_path)
                if success:
                    result[relative_path] = content

        return result
