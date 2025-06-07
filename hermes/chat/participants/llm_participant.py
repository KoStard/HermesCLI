import logging
from collections.abc import Generator
from typing import TYPE_CHECKING

from hermes.chat.participants.base import Participant

if TYPE_CHECKING:
    from hermes.chat.events import Event
    from hermes.chat.history import History
    from hermes.chat.interface import Orchestrator

logger = logging.getLogger(__name__)


class LLMParticipant(Participant):
    def __init__(self, orchestrator: "Orchestrator"):
        self.orchestrator = orchestrator

    def consume_events_and_render(self, events: Generator["Event", None, None]):
        logger.debug("Asked to consume events on LLM", self.orchestrator)
        self.orchestrator.render(events)

    def get_interface(self) -> "Orchestrator":
        return self.orchestrator

    def get_input_and_run_commands(self) -> Generator["Event", None, None]:
        logger.debug("Asked to get_input_and_run_commands on LLM", self.orchestrator)
        return self.orchestrator.get_input()

    def get_author_key(self) -> str:
        return "assistant"

    def clear(self):
        self.orchestrator.clear()

    def initialize_from_history(self, history: "History"):
        self.orchestrator.initialize_from_history(history)

    def get_name(self) -> str:
        return "assistant"

    def is_agent_mode_enabled(self) -> bool:
        from hermes.chat.interface.assistant.chat.assistant_orchestrator import ChatAssistantOrchestrator

        is_chat_interface = isinstance(self.orchestrator, ChatAssistantOrchestrator)
        return is_chat_interface and self.orchestrator.control_panel._agent_mode
