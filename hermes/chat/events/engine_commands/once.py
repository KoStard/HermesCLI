from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class OnceEvent(EngineCommandEvent):
    """Event for toggling 'once' mode - exit after completing current cycle"""

    enabled: bool

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        orchestrator.set_should_exit_after_one_cycle(self.enabled)
        status = "enabled" if self.enabled else "disabled"
        orchestrator.notifications_printer.print_notification(f"Once mode {status}")
