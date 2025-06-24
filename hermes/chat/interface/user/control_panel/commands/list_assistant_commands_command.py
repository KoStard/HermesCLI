"""List assistant commands command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.interface.helpers.terminal_coloring import CLIColors
from hermes.chat.messages import TextMessage


def _parse_list_assistant_commands_wrapper(control_panel, line: str) -> MessageEvent:
    """Wrapper for list_assistant_commands that returns an Event"""
    _parse_list_assistant_commands(control_panel, line)
    # Return a dummy event since this command doesn't produce a direct event but still needs to return one
    return MessageEvent(
        TextMessage(
            author="system",
            text="Assistant commands listed",
            is_directly_entered=False,
        ),
    )


def _parse_list_assistant_commands(control_panel, _: str) -> None:
    """List all assistant commands with their current status"""
    if not control_panel.llm_control_panel:
        control_panel.notifications_printer.print_notification("Error: LLM control panel not available", CLIColors.RED)
        return

    overrides = control_panel.llm_control_panel.get_command_override_statuses()
    commands = control_panel.llm_control_panel.get_commands()

    output = ["Assistant Commands:"]
    for cmd in commands:
        overridden_message = ""
        status = "ON" if not cmd.is_agent_command else "AGENT_ONLY"
        if cmd.command_id in overrides:
            status = overrides[cmd.command_id]
            overridden_message = " (Overridden)"
        output.append(f"- {cmd.command_id}: {status}{overridden_message}")

    control_panel.notifications_printer.print_notification("\n".join(output))

    return


def register() -> ControlPanelCommand:
    """Register the list assistant commands command."""
    return ControlPanelCommand(
        command_id="list_assistant_commands",
        command_label="/list_assistant_commands",
        description="List all assistant commands and their current status",
        short_description="Show assistant commands",
        parser=lambda line, control_panel: _parse_list_assistant_commands_wrapper(control_panel, line),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
