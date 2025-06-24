"""Switch research command for the user control panel."""

from hermes.chat.events.engine_commands import SwitchResearchEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.interface.helpers.terminal_coloring import CLIColors


def _parse_switch_research_command(control_panel, content: str) -> SwitchResearchEvent | None:
    """Parse the /switch_research command"""
    name = content.strip()
    if not name:
        control_panel.notifications_printer.print_notification(
            "Please provide the name of the research instance to switch to", CLIColors.RED
        )
        return None

    return SwitchResearchEvent(name=name)


def register() -> ControlPanelCommand:
    """Register the switch research command."""
    return ControlPanelCommand(
        command_id="switch_research",
        command_label="/switch_research",
        description="Switch to a different research instance. If the name doesn't exist, it will be created.",
        short_description="Switch research instance",
        parser=lambda line, control_panel: _parse_switch_research_command(control_panel, line),
        is_research_command=True,
        is_chat_command=False,
        is_agent_command=False,
    )
