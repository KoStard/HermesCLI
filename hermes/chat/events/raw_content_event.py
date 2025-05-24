from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.base import Event

if TYPE_CHECKING:
    from hermes.chat.messages import TextMessage, TextGeneratorMessage, ThinkingAndResponseGeneratorMessage


@dataclass
class RawContentForHistoryEvent(Event):
    content: "TextMessage | TextGeneratorMessage | ThinkingAndResponseGeneratorMessage"

    def to_json(self) -> dict:
        return {"type": "raw_content", "content": self.content.to_json()}

    @staticmethod
    def from_json(json_data: dict) -> "RawContentForHistoryEvent":
        from hermes.chat.messages import TextMessage, TextGeneratorMessage, ThinkingAndResponseGeneratorMessage

        content_type = json_data["content"]["type"]
        if content_type == "text":
            return RawContentForHistoryEvent(content=TextMessage.from_json(json_data["content"]))
        elif content_type == "text_generator":
            return RawContentForHistoryEvent(content=TextGeneratorMessage.from_json(json_data["content"]))
        elif content_type == "thinking_and_response_generator":
            return RawContentForHistoryEvent(content=ThinkingAndResponseGeneratorMessage.from_json(json_data["content"]))
        else:
            raise ValueError(f"Unknown content type: {content_type}")