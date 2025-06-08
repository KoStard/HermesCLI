import os


def prepare_filepath(filepath: str) -> str:
    """Convert various filepath formats to a normalized absolute path.

    Args:
        filepath: Input path that can be:
            - filename.extension
            - ./relative/path/filename.extension
            - ../../relative/path/filename.extension
            - /absolute/path/filename.extension
            - ~/absolute/path/filename.extension

    Returns:
        Normalized absolute path
    """
    # Expand user directory (~)
    expanded_path = os.path.expanduser(filepath)

    # Convert to absolute path if relative
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)

    # Normalize the path (resolve .. and . components)
    return os.path.normpath(expanded_path)
