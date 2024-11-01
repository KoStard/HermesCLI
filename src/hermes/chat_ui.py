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
    def __init__(self, print_pretty: bool, use_highlighting: bool, markdown_highlighter: MarkdownHighlighter, simple_input: bool):
        self.console = Console()
        self.print_pretty = print_pretty
        self.use_highlighting = use_highlighting
        self.markdown_highlighter = markdown_highlighter
        self.simple_input = simple_input
        self.prompt_toolkit_history = None

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
        return self.markdown_highlighter.process_markdown(response_generator)

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

    def get_user_input(self, prompt="You: ") -> str:
        if os.isatty(0):  # Check if input is coming from a terminal
            if self.simple_input:
                return self._get_simple_input(prompt)
            else:
                return self._get_prompt_toolkit_input(prompt)
        else:  # Input is coming from a pipe
            stdin_input = sys.stdin.read().strip()
            if stdin_input:
                return stdin_input
            else:
                return '/exit'

    def _get_simple_input(self, prompt: str) -> str:
        while True:
            self.console.print("─" * self.console.width, style="dim")
            user_input = input(prompt)
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

    def _get_prompt_toolkit_input(self, prompt: str) -> str:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        
        if self.prompt_toolkit_history is None:
            history_dir = '/tmp/hermes/'
            history_file_path = os.path.join(history_dir, 'hermes_chat_history.txt')

            if not os.path.exists(history_dir):
                os.makedirs(history_dir)
            self.prompt_toolkit_history = FileHistory(history_file_path)

        session = PromptSession(
            history=self.prompt_toolkit_history,
            auto_suggest=AutoSuggestFromHistory(),
            multiline=True,
            prompt_continuation=lambda width, line_number, is_soft_wrap: '.' * width
        )

        # Display help message only for the first input
        if not self.prompt_toolkit_history.get_strings():
            self.console.print("Tip: Press Escape + Enter to send your message.", style="bold blue")

        while True:
            self.console.print("─" * self.console.width, style="dim")
            user_input = session.prompt(prompt)
            if user_input.strip():
                return user_input
            self.console.print("Please enter a non-empty message.", style="bold red")

    def display_status(self, message: str):
        self.console.print(Panel(message, expand=False), style="bold yellow")
