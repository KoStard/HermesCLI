import os
import re


class MarkdownFilename:
    """Handles sanitization of filenames for filesystem compatibility."""

    def __init__(self, user_friendly_filename: str) -> None:
        self.user_friendly_filename = user_friendly_filename
        self.sanitized_filename = self._sanitize(user_friendly_filename)

    def get_os_aware_path(self) -> str:
        """Get a filesystem-friendly version of the filename."""
        return self.sanitized_filename

    def _sanitize(self, original_filename: str) -> str:
        """
        Sanitizes a filename to be safe for the filesystem.

        - Replaces invalid characters
        - Removes leading/trailing whitespace and punctuation
        - Replaces multiple consecutive underscores with a single one
        - Handles empty filenames

        Returns:
            A filesystem-safe version of the filename
        """
        original_filename = original_filename.strip()
        if not original_filename:
            import uuid

            # Generate a unique name for empty filename
            return "unnamed_" + str(uuid.uuid4())

        # Separate base name and extension
        base_name, extension = os.path.splitext(original_filename)
        extension = extension.lower()

        # Basic sanitization
        sanitized_base = re.sub(r'[<>:"/\\|?*]+', "_", base_name)
        sanitized_base = re.sub(r"\s+", "_", sanitized_base)
        sanitized_base = re.sub(r"_+", "_", sanitized_base)
        sanitized_base = re.sub(r"[^a-zA-Z0-9_-]+", "", sanitized_base)
        sanitized_base = re.sub(r"^[._-]+|[._-]+$", "", sanitized_base)

        if not sanitized_base:
            sanitized_base = "sanitized"

        # Ensure we have a .md extension for markdown files
        if not extension or extension != ".md":
            extension = ".md"

        return sanitized_base + extension
