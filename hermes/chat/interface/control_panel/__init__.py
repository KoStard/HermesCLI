from collections.abc import Callable
from dataclasses import dataclass

from hermes.chat.events.base import Event


@dataclass
class ControlPanelCommand:
    command_id: str  # The unique ID of the command which will be used in configuration
    command_label: str
    description: str
    short_description: str
    parser: Callable[[str], Event | None]
    priority: int = 0
    with_argument: bool = True
    # For user commands only
    visible_from_cli: bool = True
    visible_from_interface: bool = True
    default_on_cli: bool = False
    is_chat_command: bool = True
    # For assistant commands
    is_agent_command: bool = False
    # For deep research
    is_research_command: bool = False
