from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class ThinkingLevelEvent(EngineCommandEvent):
    count: int

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        orchestrator.assistant_participant.get_interface().change_thinking_level(self.count)
        orchestrator.notifications_printer.print_notification(f"Thinking level set to {self.count}")
