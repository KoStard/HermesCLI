"""Budget command for the user control panel."""

from hermes.chat.events.engine_commands import DeepResearchBudgetEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.interface.helpers.terminal_coloring import CLIColors


def _parse_budget_command(control_panel, content: str) -> DeepResearchBudgetEvent | None:
    """Parse the /budget command"""
    try:
        budget = int(content.strip())
        if budget <= 0:
            control_panel.notifications_printer.print_notification("Budget must be a positive integer", CLIColors.RED)
            return None
        return DeepResearchBudgetEvent(budget=budget)
    except ValueError:
        control_panel.notifications_printer.print_notification(
            "Invalid budget value. Please provide a positive integer.",
            CLIColors.RED,
        )
        return None


def register() -> ControlPanelCommand:
    """Register the budget command."""
    return ControlPanelCommand(
        command_id="budget",
        command_label="/budget",
        description=(
            "Set a hard budget limit for Deep Research Assistant (number of message cycles). "
            "Set negative number to remove the budget. "
            "Default is 30. "
            "You'll be asked if you want to continue if the assistant exhausts the budget."
        ),
        short_description="Set Deep Research budget",
        parser=lambda line, control_panel: _parse_budget_command(control_panel, line),
        is_research_command=True,
        is_chat_command=False,
        is_agent_command=False,
    )
