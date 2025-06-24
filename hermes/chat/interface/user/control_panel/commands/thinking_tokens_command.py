"""Thinking tokens command for the user control panel."""

from hermes.chat.events.engine_commands import ThinkingLevelEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the thinking tokens command."""
    return ControlPanelCommand(
        command_id="thinking_tokens",
        command_label="/thinking_tokens",
        description="Set the thinking tokens (number)",
        short_description="Set thinking tokens",
        parser=lambda line, control_panel: ThinkingLevelEvent(count=int(line.strip().lower())),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=True,
    )
