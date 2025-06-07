from dataclasses import dataclass

from hermes.chat.events import Event
from hermes.chat.messages import Message


@dataclass(init=False)
class HistoryRecoveryEvent(Event):
    messages: list[Message]

    def __init__(self, messages: list[Message]):
        self.messages = messages

    def get_messages(self) -> list[Message]:
        return self.messages
