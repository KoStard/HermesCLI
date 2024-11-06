"""
Goal:
- Detect user input with keys up and down
- Use the whole screen of terminal for rendering the UI and showing the options
- Allow navigating the options with the arrow keys up and down
- Allow selecting an option with the enter key
- Use no external libraries for rendering the UI or handling input
"""

import os

# Get the size of the terminal
os.get_terminal_size()

print(os.name)
# Possible values and their meaning:
# posix - Unix and Linux
# nt - Windows
# etc

import termios

termios.tcgetattr(0)
import sys
import tty

