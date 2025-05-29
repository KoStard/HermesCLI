from dataclasses import dataclass
from datetime import datetime

from hermes.chat.messages.base import Message


@dataclass(init=False)
class TextMessage(Message):
    """Class for regular text messages"""

    text: str
    is_directly_entered: bool
    name: str | None
    text_role: str | None

    def __init__(
        self,
        *,
        author: str,
        text: str,
        timestamp: datetime | None = None,
        is_directly_entered: bool = False,
        name: str | None = None,
        text_role: str | None = None,
    ):
        super().__init__(author=author, timestamp=timestamp)
        self.text = text
        self.is_directly_entered = is_directly_entered
        self.name = name
        self.text_role = text_role

    def get_content_for_user(self) -> str:
        return self.text

    def get_content_for_assistant(self) -> str:
        return self.text

    def to_json(self) -> dict:
        return {
            "type": "text",
            "text": self.text,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "is_directly_entered": self.is_directly_entered,
            "name": self.name,
            "text_role": self.text_role,
        }

    @staticmethod
    def from_json(json_data: dict) -> "TextMessage":
        return TextMessage(
            author=json_data["author"],
            text=json_data["text"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            is_directly_entered=json_data["is_directly_entered"],
            name=json_data.get("name"),
            text_role=json_data.get("text_role"),
        )


@dataclass(init=False)
class InvisibleMessage(TextMessage):
    """Class for messages that are invisible to the user"""

    def get_content_for_user(self) -> str:
        return ""


@dataclass(init=False)
class AssistantNotificationMessage(TextMessage):
    """Class for notifications visible only to the assistant, not the user"""

    def __init__(
        self,
        *,
        text: str,
        timestamp: datetime | None = None,
        name: str | None = None,
    ):
        super().__init__(
            author="user",
            text=text,
            timestamp=timestamp,
            is_directly_entered=True,
            name=name,
            text_role="notification",
        )

    def get_content_for_user(self) -> str:
        # Not visible to the user
        return ""

    def to_json(self) -> dict:
        data = super().to_json()
        data["type"] = "assistant_notification"
        return data

    @staticmethod
    def from_json(json_data: dict) -> "AssistantNotificationMessage":
        return AssistantNotificationMessage(
            text=json_data["text"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            name=json_data.get("name"),
        )
