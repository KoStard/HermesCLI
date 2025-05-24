from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.interface.helpers.cli_notifications import CLIColors

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class DeepResearchBudgetEvent(EngineCommandEvent):
    """Event for setting a budget for Deep Research Assistant"""

    budget: int

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        if hasattr(orchestrator.assistant_participant.get_interface(), "set_budget"):
            orchestrator.assistant_participant.get_interface().set_budget(self.budget)
            orchestrator.notifications_printer.print_notification(f"Deep Research budget set to {self.budget} message cycles")
        else:
            orchestrator.notifications_printer.print_notification(
                "Budget setting is only available for Deep Research Assistant",
                CLIColors.YELLOW,
            )