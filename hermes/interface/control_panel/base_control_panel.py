"""
Interface alone can handle text input and output
Control panel is a part of the interface that handles user interaction
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generator, Optional
from .peekable_generator import PeekableGenerator
from hermes.message import Message, TextMessage, TextGeneratorMessage
from hermes.event import Event

@dataclass
class ControlPanelCommand:
    command_label: str
    description: str
    parser: Callable[[str], Event]
    priority: int = 0
    # For user commands only
    visible_from_cli: bool = True
    default_on_cli: bool = False

class ControlPanel(ABC):
    def __init__(self):
        self.commands = {}
        self.help_contents = []

    @abstractmethod
    def render(self) -> str:
        pass

    @abstractmethod
    def break_down_and_execute_message(self, message: Message) -> Generator[Event, None, None]:
        pass

    def _register_command(self, command: ControlPanelCommand):
        """
        Register a command that can be executed by a participant
        The parser will receive a line that starts with the command
        """
        self.commands[command.command_label] = command

    def _add_help_content(self, content: str):
        self.help_contents.append(content)
    
    def _render_help_content(self) -> str:
        return "\n".join(self.help_contents)

    def _render_command_in_control_panel(self, command_label: str) -> str:
        return f"{command_label} - {self.commands[command_label].description}"
    
    def _lines_from_message(self, message: Message) -> Generator[str, None, None]:
        if isinstance(message, TextMessage):
            for line in message.text.split("\n"):
                yield line + "\n"
        elif isinstance(message, TextGeneratorMessage):
            buffer = ""
            for chunk in message.get_content_for_user():
                buffer += chunk
                while "\n" in buffer:
                    yield buffer[:buffer.index("\n")] + "\n"
                    buffer = buffer[buffer.index("\n") + 1:]
            if buffer:
                yield buffer + "\n"
    
    def _line_command_match(self, line: str) -> Optional[str]:
        line = line.strip()
        for command_label in self.commands:
            if line.startswith(command_label + " ") or line == command_label:
                return command_label
        return None

    def _extract_command_content_in_line(self, command_label: str, line: str) -> str:
        return line[len(command_label):].strip()
