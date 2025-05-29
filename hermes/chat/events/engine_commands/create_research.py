from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.interface.helpers.terminal_coloring import CLIColors

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class CreateResearchEvent(EngineCommandEvent):
    """Event to create a new research instance and switch to it"""

    name: str

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        """Create a new research instance and switch to it"""
        if hasattr(orchestrator.assistant_participant.interface, "create_new_research"):
            try:
                orchestrator.assistant_participant.interface.create_new_research(self.name)
                orchestrator.notifications_printer.print_notification(f"Created and switched to new research instance: {self.name}")
            except ValueError as e:
                orchestrator.notifications_printer.print_notification(str(e), CLIColors.RED)
        else:
            orchestrator.notifications_printer.print_notification("Research management is not available in this mode", CLIColors.RED)
