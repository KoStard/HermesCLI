from rich.console import Console
from rich.markdown import Markdown
from rich import live as Live
from rich.spinner import Spinner
from rich.panel import Panel
from typing import Generator
import os

class ChatUI:
    def __init__(self, prints_raw: bool):
        self.console = Console()
        self.prints_raw = prints_raw

    def display_response(self, response_generator: Generator[str, None, None]):
        if self.prints_raw:
            buffer = ""
            for text in response_generator:
                buffer += text
                print(text, end="", flush=True)
            print()
            return buffer
        
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
        while True:
            self.console.print("─" * self.console.width, style="dim")
            user_input = self.console.input("[bold cyan]You:[/bold cyan] ")
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

    def display_status(self, message: str):
        self.console.print(Panel(message, expand=False), style="bold yellow")

    def clear_screen(self):
        # This method is now only used to display a message about clearing chat history
        self.console.print("Chat history has been cleared.", style="bold green")
