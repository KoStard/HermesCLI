from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.interface.assistant.deep_research.assistant_orchestrator import DeepResearchAssistantOrchestrator
from hermes.chat.interface.helpers.terminal_coloring import CLIColors

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class PrintResearchStatusEvent(EngineCommandEvent):
    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        assistant_interface = orchestrator.assistant_participant.get_interface()
        if not isinstance(assistant_interface, DeepResearchAssistantOrchestrator):
            orchestrator.notifications_printer.print_notification(
                "Command supported only for Deep Research Assistant",
                CLIColors.YELLOW,
            )
            return
        engine = assistant_interface.get_engine()
        status_printer = engine.status_printer
        status_printer.print_status(engine.research)
