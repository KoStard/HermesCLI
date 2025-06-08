"""Goal:
- Print into the CLI notifications/status messages.
- Have the first implementation, which prints the given message to the CLI in a round rectangle.
"""

from hermes.chat.interface.helpers.terminal_coloring import CLIColors, colorize_text
from hermes.chat.interface.helpers.terminal_window import get_terminal_size


class CLINotificationsPrinter:
    def __init__(self):
        pass

    def print_notification(self, message: str, color: CLIColors = CLIColors.YELLOW):
        import textwrap

        # Get terminal size
        terminal_width, _ = get_terminal_size()

        # Define padding and calculate box width
        padding = 4
        max_message_width = terminal_width - padding

        lines = message.split("\n")

        wrapped_message = [wrapped_line for line in lines for wrapped_line in textwrap.wrap(line, width=max_message_width - 4)]

        # Determine the width of the box based on the longest line
        box_width = min(max(len(line) for line in wrapped_message) + 4, terminal_width)

        # Top border with rounded corners
        top_border = "╭" + "─" * (box_width - 2) + "╮"
        print(colorize_text(top_border, color))

        # Message lines
        for line in wrapped_message:
            # Center the text within the box
            centered_line = line.center(box_width - 4)
            print(colorize_text(f"│ {centered_line} │", color))

        # Bottom border with rounded corners
        bottom_border = "╰" + "─" * (box_width - 2) + "╯"
        print(colorize_text(bottom_border, color))

    def print_error(self, message: str):
        self.print_notification(message, CLIColors.RED)


if __name__ == "__main__":
    printer = CLINotificationsPrinter()
    printer.print_notification("This is a test message that should be printed in a round rectangle.")
