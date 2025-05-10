import os
import re


class Filename:
    """Handles sanitization of filenames for filesystem compatibility."""

    def __init__(self, user_friendly_filename: str) -> None:
        self.user_friendly_filename = user_friendly_filename
        self.sanitized_filename = self._sanitize(user_friendly_filename)

    def get_os_aware_path(self) -> str:
        """Get a filesystem-friendly version of the filename."""
        return self.sanitized_filename

    def _sanitize(self, original_filename: str) -> str:
        """Sanitize a filename for filesystem compatibility."""
        # TODO: Handle windows max length
        original_filename = original_filename.strip()
        if not original_filename:
            raise ValueError("Empty filename provided")

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

        return sanitized_base
