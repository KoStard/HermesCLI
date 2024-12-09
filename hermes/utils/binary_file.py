import os

def is_binary(file_path):
    """
    Determine if a file is binary or text by checking for non-printable characters.

    :param file_path: Path to the file.
    :return: True if the file is likely binary, False if it is likely text.
    """
    NULL_BYTE = b'\x00'

    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, 'rb') as f:
            # Read a small portion of the file
            sample = f.read(1024)

        # Check for null bytes, which are common in binary files
        if NULL_BYTE in sample:
            return True

        # Try to decode as UTF-8, which covers all Unicode characters
        try:
            sample.decode('utf-8')
            return False
        except UnicodeDecodeError:
            return True

    except OSError:
        # If we encounter an error reading the file, assume it's binary
        return True
