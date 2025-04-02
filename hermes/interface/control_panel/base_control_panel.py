"""
Interface alone can handle text input and output
Control panel is a part of the interface that handles user interaction
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generator, Optional, List

from hermes.interface.helpers.chunks_to_lines import chunks_to_lines
from ..helpers.peekable_generator import PeekableGenerator
from hermes.message import Message, TextMessage, TextGeneratorMessage
from hermes.event import Event


@dataclass
class ControlPanelCommand:
    command_id: str  # The unique ID of the command which will be used in configuration
    command_label: str
    description: str
    short_description: str
    parser: Callable[[str], Event]
    priority: int = 0
    with_argument: bool = True
    # For user commands only
    visible_from_cli: bool = True
    default_on_cli: bool = False
    # For assistant commands
    is_agent_command: bool = False
    # For deep research
    is_deep_research: bool = False


class ControlPanel(ABC):
    def __init__(self):
        self.commands = {}
        self.help_contents = []

    @abstractmethod
    def render(self) -> str:
        pass

    @abstractmethod
    def break_down_and_execute_message(
        self, message: Message
    ) -> Generator[Event, None, None]:
        pass

    def _register_command(self, command: ControlPanelCommand):
        """
        Register a command that can be executed by a participant
        The parser will receive a line that starts with the command
        """
        self.commands[command.command_label] = command

    def _add_help_content(self, content: str, is_agent_only: bool = False):
        self.help_contents.append((content, is_agent_only))

    def _render_help_content(self, is_agent_mode: bool = False) -> str:
        filtered_contents = [
            content
            for content, agent_only in self.help_contents
            if not agent_only or is_agent_mode
        ]
        return "\n".join(filtered_contents)

    def _render_command_in_control_panel(self, command_label: str) -> str:
        return f"{command_label} - {self.commands[command_label].description}"

    def _lines_from_message(self, message: Message) -> Generator[str, None, None]:
        return chunks_to_lines(message.get_content_for_user())

    def _line_command_match(self, line: str) -> Optional[str]:
        line = line.strip()
        for command_label in self.commands:
            if line.startswith(command_label + " ") or line == command_label:
                return command_label
        return None

    def _extract_command_content_in_line(self, command_label: str, line: str) -> str:
        return line[len(command_label) :].strip()

    def get_commands(self) -> List[ControlPanelCommand]:
        return self.commands.values()
