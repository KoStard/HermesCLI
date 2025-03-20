def get_file_extension(file_path: str) -> str:
    return file_path.split(".")[-1]


def remove_quotes(path: str) -> str:
    """
    Remove various types of quotes from the path.

    Args:
        path: Input path that might contain quotes

    Returns:
        Path with quotes removed
    """
    # Remove single quotes, double quotes, and smart quotes
    quotes = {"'", '"', """, """}

    # Trim quotes from beginning and end of path
    while path and path[0] in quotes:
        path = path[1:]
    while path and path[-1] in quotes:
        path = path[:-1]

    return path
