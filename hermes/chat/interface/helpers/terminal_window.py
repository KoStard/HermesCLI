"""
This module is responsible for getting information about the terminal window, like size.
"""

import os


def get_terminal_size() -> tuple[int, int]:
    """
    Get the size of the terminal window.

    Returns:
        tuple[int, int]: A tuple containing the number of rows and columns in the terminal.
    """
    try:
        rows, columns = os.get_terminal_size()
    except Exception as e:
        print(f"Error getting terminal size: {e}")
        rows, columns = 100, 100
    return rows, columns


if __name__ == "__main__":
    print(get_terminal_size())
