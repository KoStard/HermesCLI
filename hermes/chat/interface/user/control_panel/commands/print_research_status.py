from hermes.chat.events.engine_commands.print_research_status import PrintResearchStatusEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    print("HERE")
    return ControlPanelCommand(
        command_id="print_research_status",
        command_label="/print_research_status",
        description="Print the research status",
        short_description="Print the research status",
        parser=lambda line, user_control_panel: PrintResearchStatusEvent(),
        visible_from_cli=False,
        is_chat_command=False,
        is_agent_command=False,
        is_research_command=True,
    )
