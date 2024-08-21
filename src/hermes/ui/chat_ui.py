from rich.console import Console
from rich.markdown import Markdown
from rich import live as Live
from rich.spinner import Spinner
from typing import Generator

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
            user_input = input("You: ").strip()
            if user_input:
                return user_input
            print("Please enter a non-empty message.")

    def display_status(self, message: str):
        self.console.print(message)
