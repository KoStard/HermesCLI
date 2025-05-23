from collections.abc import Generator

from hermes.chat.event import Event
from hermes.chat.interface.assistant.chat_assistant.interface import ChatAssistantInterface
from hermes.chat.message import TextMessage
from hermes.chat.participants import Participant


class AssistantModeManager:
    def __init__(self, assistant_participant: Participant):
        self.assistant_participant = assistant_participant

    def should_continue_assistant_turn(self) -> bool:
        return self._is_agent_mode_enabled()

    def get_continuation_message_if_needed(self, is_first_cycle: bool) -> Generator[Event, None, None]:
        if self._is_agent_mode_enabled() and not is_first_cycle:
            from hermes.chat.event import MessageEvent
            
            continuation_msg = TextMessage(
                author="user",
                text="AUTOMATIC RESPONSE: No ///done command found in your repsonse. "
                "Please continue, and use ///done command when you finish with the whole task.",
                is_directly_entered=True,
            )
            return [MessageEvent(continuation_msg)]
        return []

    def _is_agent_mode_enabled(self) -> bool:
        is_chat_interface = isinstance(self.assistant_participant.interface, ChatAssistantInterface)
        return is_chat_interface and self.assistant_participant.interface.control_panel._agent_mode