from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(init=False)
class Message(ABC):
    """
    Base abstract class for all message types
    A single message might represent only a part of the message
    During one interaction, a single participant might send multiple messages
    """

    author: str
    timestamp: datetime

    def __init__(self, *, author: str, timestamp: datetime | None = None):
        self.author = author
        self.timestamp = timestamp or datetime.now()

    @abstractmethod
    def get_content_for_user(self) -> str | Generator[str]:
        pass

    @abstractmethod
    def get_content_for_assistant(self) -> Any:
        pass

    @abstractmethod
    def to_json(self) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def from_json(json_data: dict) -> "Message":
        pass
