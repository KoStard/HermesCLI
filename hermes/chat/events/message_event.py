from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.base import Event

if TYPE_CHECKING:
    from hermes.chat.messages import Message


@dataclass(init=False)
class MessageEvent(Event):
    """Message events are events that contain a message and are sent to the next participant."""

    message: "Message"

    def __init__(self, message: "Message"):
        self.message = message

    def get_message(self) -> "Message":
        return self.message
