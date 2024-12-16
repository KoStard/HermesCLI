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
    quotes = {"'", '"', '“', '”'}
    result = []
    for c in path:
        if c not in quotes:
            result.append(c)
    return ''.join(result)