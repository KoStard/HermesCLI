from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.interface.helpers.terminal_coloring import CLIColors

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class ListResearchEvent(EngineCommandEvent):
    """Event to list all research instances"""

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        """List all research instances"""
        if hasattr(orchestrator.assistant_participant.interface, 'list_research_instances'):
            try:
                instances = orchestrator.assistant_participant.interface.list_research_instances()
                current = None
                if hasattr(orchestrator.assistant_participant.interface, 'get_current_research_name'):
                    current = orchestrator.assistant_participant.interface.get_current_research_name()
                
                if not instances:
                    orchestrator.notifications_printer.print_notification(
                        "No research instances found"
                    )
                else:
                    output = ["Research instances:"]
                    for name in instances:
                        marker = " (current)" if name == current else ""
                        output.append(f"  - {name}{marker}")
                    orchestrator.notifications_printer.print_notification("\n".join(output))
            except ValueError as e:
                orchestrator.notifications_printer.print_notification(
                    str(e), CLIColors.RED
                )
        else:
            orchestrator.notifications_printer.print_notification(
                "Research management is not available in this mode",
                CLIColors.RED
            )
