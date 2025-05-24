from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass(init=False)
class ExitEvent(EngineCommandEvent):
    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        raise EOFError