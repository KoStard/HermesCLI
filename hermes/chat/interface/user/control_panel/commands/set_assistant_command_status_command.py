"""Set assistant command status command for the user control panel."""

from hermes.chat.events.base import Event
from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.interface.helpers.terminal_coloring import CLIColors
from hermes.chat.messages import TextMessage


def _parse_set_assistant_command_status_wrapper(control_panel, content: str) -> Event:
    """Wrapper for set_assistant_command_status that returns an Event"""
    _parse_set_assistant_command_status(control_panel, content)
    # Return a MessageEvent as this command doesn't produce a direct event
    return MessageEvent(
        TextMessage(
            author="system",
            text="Assistant command status updated",
            is_directly_entered=False,
        ),
    )


def _parse_set_assistant_command_status(control_panel, content: str) -> None:
    """Set the status of an assistant command"""
    if not control_panel.llm_control_panel:
        control_panel.notifications_printer.print_notification("Error: LLM control panel not available", CLIColors.RED)
        return

    try:
        command_id, status = content.strip().split()
        control_panel.llm_control_panel.set_command_override_status(command_id, status)
    except ValueError:
        control_panel.notifications_printer.print_notification(
            "Error: Invalid format. Use: /set_assistant_command_status <command_id> <status>",
            CLIColors.RED,
        )
    return


def register() -> ControlPanelCommand:
    """Register the set assistant command status command."""
    return ControlPanelCommand(
        command_id="set_assistant_command_status",
        command_label="/set_assistant_command_status",
        description="Set the status of an assistant command (ON/OFF/AGENT_ONLY)",
        short_description="Set assistant command status",
        parser=lambda line, control_panel: _parse_set_assistant_command_status_wrapper(control_panel, line),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
