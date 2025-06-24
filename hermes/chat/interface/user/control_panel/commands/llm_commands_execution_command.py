"""LLM commands execution command for the user control panel."""

from hermes.chat.events.engine_commands import LLMCommandsExecutionEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the llm commands execution command."""
    return ControlPanelCommand(
        command_id="llm_commands_execution",
        command_label="/llm_commands_execution",
        description="Enable or disable execution of LLM commands (on/off)",
        short_description="Toggle LLM command execution",
        parser=lambda line, control_panel: LLMCommandsExecutionEvent(enabled=line.strip().lower() == "on"),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
