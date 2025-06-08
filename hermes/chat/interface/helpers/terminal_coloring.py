"""Task:
- Provide functions that colorize the text that will be printed into the CLI.
- Use the ANSI escape codes for coloring.
- Define the colors as enum.
"""

from enum import Enum


class CLIColors(Enum):
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def colorize_text(text: str, color: CLIColors) -> str:
    return f"{color.value}{text}\033[0m"


def print_colored_text(text: str, color: CLIColors, **kwargs) -> None:
    print(colorize_text(text, color), **kwargs)


if __name__ == "__main__":
    for color in CLIColors:
        print_colored_text(f"Hello, world! ({color.name})", color)
