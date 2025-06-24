"""Save history command for the user control panel."""

from hermes.chat.events.engine_commands import SaveHistoryEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the save history command."""
    return ControlPanelCommand(
        command_id="save_history",
        command_label="/save_history",
        description="Save history to a file",
        short_description="Save chat history",
        parser=lambda line: SaveHistoryEvent(line),
        visible_from_cli=False,
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
