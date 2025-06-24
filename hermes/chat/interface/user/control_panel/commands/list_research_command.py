"""List research command for the user control panel."""

from hermes.chat.events.engine_commands import ListResearchEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the list research command."""
    return ControlPanelCommand(
        command_id="list_research",
        command_label="/list_research",
        description="List all research instances (Deep Research mode only)",
        short_description="List research instances",
        parser=lambda line, control_panel: ListResearchEvent(),
        with_argument=False,
        is_research_command=True,
        is_chat_command=False,
        is_agent_command=False,
    )
