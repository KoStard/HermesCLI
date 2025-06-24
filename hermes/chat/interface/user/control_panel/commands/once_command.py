"""Once command for the user control panel."""

from hermes.chat.events.engine_commands import OnceEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the once command."""
    return ControlPanelCommand(
        command_id="once",
        command_label="/once",
        description="Enable or disable once mode - exit after completing current cycle (on/off)",
        short_description="Toggle once mode",
        parser=lambda line: OnceEvent(enabled=line.strip().lower() == "on"),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=True,
    )
