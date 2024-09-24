from rich.console import Console
from rich.markdown import Markdown
from rich import live as Live
from rich.spinner import Spinner
from rich.panel import Panel
from typing import Generator
import os
import sys
from .utils.markdown_highlighter import MarkdownHighlighter

class ChatUI:
    def __init__(self, print_pretty: bool, use_highlighting: bool):
        self.console = Console()
        self.print_pretty = print_pretty
        self.use_highlighting = use_highlighting
        self.markdown_highlighter = MarkdownHighlighter()

    def display_response(self, response_generator: Generator[str, None, None]):
        if self.print_pretty:
            return self._display_pretty_response(response_generator)
        elif self.use_highlighting:
            return self._display_highlighted_response(response_generator)
        else:
            return self._display_raw_response(response_generator)

    def _display_raw_response(self, response_generator: Generator[str, None, None]):
        buffer = []
        for text in response_generator:
            buffer.append(text)
            print(text, end="", flush=True)
        print()
        return ''.join(buffer)

    def _display_highlighted_response(self, response_generator: Generator[str, None, None]):
        buffer = []
        for text in response_generator:
            buffer.append(text)
        full_response = ''.join(buffer)
        self.markdown_highlighter.process_markdown(full_response)
        return full_response

    def _display_pretty_response(self, response_generator: Generator[str, None, None]):
        with Live.Live(console=self.console, auto_refresh=False) as live:
            live.update(Spinner("dots", text="Assistant is thinking..."))

            buffer = ""
            for text in response_generator:
                buffer += text
                live.update(Markdown("Assistant: \n" + buffer))
                live.refresh()

            live.update(Markdown("Assistant: \n" + buffer))
        return buffer

    def get_user_input(self) -> str:
        if os.isatty(0):  # Check if input is coming from a terminal
            while True:
                self.console.print("─" * self.console.width, style="dim")
                user_input = input("You: ")
                if user_input.strip() == "{":
                    lines = []
                    while True:
                        line = self.console.input()
                        if line.strip() == "}":
                            break
                        lines.append(line)
                    user_input = "\n".join(lines)
                if user_input.strip():
                    return user_input
                self.console.print("Please enter a non-empty message.", style="bold red")
        else:  # Input is coming from a pipe
            return sys.stdin.read().strip()

    def display_status(self, message: str):
        self.console.print(Panel(message, expand=False), style="bold yellow")
