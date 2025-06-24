"""Focus subproblem command for the user control panel."""

from hermes.chat.events.engine_commands import FocusSubproblemEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the focus subproblem command."""
    return ControlPanelCommand(
        command_id="focus_subproblem",
        command_label="/focus_subproblem",
        description="Change focus to a specific subproblem in the research tree (Deep Research mode only)",
        short_description="Focus on a subproblem",
        parser=lambda line, control_panel: FocusSubproblemEvent(node_id="SHOW_SELECTOR"),
        with_argument=False,
        is_research_command=True,
        is_chat_command=False,
        is_agent_command=False,
    )
