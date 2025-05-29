from dataclasses import dataclass
from datetime import datetime

from hermes.chat.messages.base import Message


@dataclass(init=False)
class UrlMessage(Message):
    """Class for messages that are urls"""

    url: str

    def __init__(self, *, author: str, url: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.url = url

    def get_content_for_user(self) -> str:
        return f"URL: {self.url}"

    def get_content_for_assistant(self) -> str:
        return self.url

    def to_json(self) -> dict:
        return {
            "type": "url",
            "url": self.url,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "UrlMessage":
        return UrlMessage(
            author=json_data["author"],
            url=json_data["url"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )
