"""Agent mode command for the user control panel."""

from hermes.chat.events.engine_commands import AgentModeEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the agent mode command."""
    return ControlPanelCommand(
        command_id="agent_mode",
        command_label="/agent_mode",
        description="Enable or disable agent mode (on/off)",
        short_description="Toggle agent mode",
        parser=lambda line, control_panel: AgentModeEvent(enabled=line.strip().lower() == "on"),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
