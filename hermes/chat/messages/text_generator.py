from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from hermes.chat.messages.base import Message


@dataclass(init=False)
class TextGeneratorMessage(Message):
    """Class for messages that contain a text generator"""

    text_generator: Iterable[str]
    text: str
    has_finished: bool
    is_directly_entered: bool
    name: str | None
    text_role: str | None

    def __init__(
        self,
        *,
        author: str,
        text_generator: Iterable[str],
        timestamp: datetime | None = None,
        is_directly_entered: bool = False,
        name: str | None = None,
        text_role: str | None = None,
    ):
        super().__init__(author=author, timestamp=timestamp)
        # We should track the output of the generator, and save it to self.text
        self.text_generator = text_generator
        self.text = ""
        self.has_finished = False
        self.is_directly_entered = is_directly_entered
        self.name = name
        self.text_role = text_role

    def get_content_for_user(self) -> Generator[str, None, None]:
        # Yield each new chunk from the generator and accumulate in self.text
        if self.text:
            yield self.text
        if not self.has_finished:
            for chunk in self.text_generator:
                self.text += chunk
                yield chunk
            self.has_finished = True

    def get_content_for_assistant(self) -> str:
        for chunk in self.text_generator:
            self.text += chunk

        return self.text

    def to_json(self) -> dict:
        return {
            "type": "text_generator",
            "text": self.text,
            "has_finished": self.has_finished,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "is_directly_entered": self.is_directly_entered,
            "name": self.name,
            "text_role": self.text_role,
        }

    @staticmethod
    def from_json(json_data: dict) -> "TextGeneratorMessage":
        # Since we can't serialize a generator, we'll create a simple generator that yields the stored text
        def text_gen():
            yield json_data["text"]

        msg = TextGeneratorMessage(
            author=json_data["author"],
            text_generator=text_gen(),
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            is_directly_entered=json_data.get("is_directly_entered", False),
            name=json_data.get("name"),
            text_role=json_data.get("text_role"),
        )
        msg.text = json_data["text"]
        msg.has_finished = json_data["has_finished"]
        return msg
