"""Exit command for the user control panel."""

from hermes.chat.events.engine_commands import ExitEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the exit command."""
    return ControlPanelCommand(
        command_id="exit",
        command_label="/exit",
        description="Exit the application",
        short_description="Exit Hermes",
        parser=lambda _: ExitEvent(),
        priority=-100,  # Run exit after running any other command
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=True,
    )
