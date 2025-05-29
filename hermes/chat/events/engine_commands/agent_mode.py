from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class AgentModeEvent(EngineCommandEvent):
    enabled: bool

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        if self.enabled:
            orchestrator.assistant_participant.get_interface().control_panel.enable_agent_mode()
            orchestrator.notifications_printer.print_notification("Agent mode enabled")
        else:
            orchestrator.assistant_participant.get_interface().control_panel.disable_agent_mode()
            orchestrator.notifications_printer.print_notification("Agent mode disabled")
