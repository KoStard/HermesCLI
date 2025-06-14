from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.interface.assistant.deep_research.assistant_orchestrator import DeepResearchAssistantOrchestrator
from hermes.chat.interface.helpers.terminal_coloring import CLIColors

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class SwitchResearchEvent(EngineCommandEvent):
    """Event to switch to a different research instance"""

    name: str

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        """Switch to a different research instance"""
        if isinstance(orchestrator.assistant_participant.orchestrator, DeepResearchAssistantOrchestrator):
            try:
                orchestrator.assistant_participant.orchestrator.switch_research(self.name)
                orchestrator.notifications_printer.print_notification(f"Switched to research instance: {self.name}")
            except ValueError as e:
                orchestrator.notifications_printer.print_notification(str(e), CLIColors.RED)
        else:
            orchestrator.notifications_printer.print_notification("Research management is not available in this mode", CLIColors.RED)
