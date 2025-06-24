"""Load history command for the user control panel."""

from hermes.chat.events.engine_commands import LoadHistoryEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the load history command."""
    return ControlPanelCommand(
        command_id="load_history",
        command_label="/load_history",
        description="Load history from a file",
        short_description="Load chat history",
        parser=lambda line: LoadHistoryEvent(line),
        priority=98,
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
