from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class AssistantDoneEvent(EngineCommandEvent):
    """Event emitted when the assistant marks a task as done in agent mode"""

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        orchestrator.notifications_printer.print_notification("Assistant marked task as done")
        orchestrator._received_assistant_done_event = True