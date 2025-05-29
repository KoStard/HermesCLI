from dataclasses import dataclass

from hermes.chat.events.base import Event


@dataclass(init=False)
class NotificationEvent(Event):
    """Notification events are events that contain a notification and are sent to the next participant."""

    text: str

    def __init__(self, text: str):
        self.text = text
