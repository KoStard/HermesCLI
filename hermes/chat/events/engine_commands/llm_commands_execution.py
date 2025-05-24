from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class LLMCommandsExecutionEvent(EngineCommandEvent):
    """Event for toggling LLM command execution"""

    enabled: bool

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        orchestrator.assistant_participant.get_interface().control_panel.set_commands_parsing_status(self.enabled)
        status = "enabled" if self.enabled else "disabled"
        orchestrator.notifications_printer.print_notification(f"LLM command execution {status}")