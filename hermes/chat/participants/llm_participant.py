import logging
from collections.abc import Generator
from typing import TYPE_CHECKING

from hermes.chat.participants.base import Participant

if TYPE_CHECKING:
    from hermes.chat.events import Event
    from hermes.chat.history import History
    from hermes.chat.interface import Interface
    from hermes.chat.messages import Message

logger = logging.getLogger(__name__)


class LLMParticipant(Participant):
    def __init__(self, interface: "Interface"):
        self.interface = interface

    def consume_events_and_render(self, history_snapshot: list["Message"], events: Generator["Event", None, None]):
        logger.debug("Asked to consume events on LLM", self.interface)
        self.interface.render(history_snapshot, events)

    def get_interface(self) -> "Interface":
        return self.interface

    def get_input_and_run_commands(self) -> Generator["Event", None, None]:
        logger.debug("Asked to get_input_and_run_commands on LLM", self.interface)
        return self.interface.get_input()

    def get_author_key(self) -> str:
        return "assistant"

    def clear(self):
        self.interface.clear()

    def initialize_from_history(self, history: "History"):
        self.interface.initialize_from_history(history)

    def get_name(self) -> str:
        return "assistant"

    def is_agent_mode_enabled(self) -> bool:
        from hermes.chat.interface.assistant.chat_assistant.interface import ChatAssistantInterface
        
        is_chat_interface = isinstance(self.interface, ChatAssistantInterface)
        return is_chat_interface and self.interface.control_panel._agent_mode