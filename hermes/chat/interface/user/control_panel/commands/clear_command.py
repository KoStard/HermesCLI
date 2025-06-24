"""Clear command for the user control panel."""

from hermes.chat.events.engine_commands import ClearHistoryEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the clear command."""
    return ControlPanelCommand(
        command_id="clear",
        command_label="/clear",
        description="Clear the conversation history",
        short_description="Clear chat history",
        parser=lambda line, control_panel: ClearHistoryEvent(),
        priority=99,  # Clear history should be first
        visible_from_cli=False,
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
