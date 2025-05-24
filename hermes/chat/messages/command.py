from dataclasses import dataclass
from datetime import datetime

from hermes.chat.messages.base import Message


@dataclass(init=False)
class LLMRunCommandOutput(Message):
    """Class for messages that represent the output of LLM-run commands"""

    text: str
    name: str | None

    def __init__(
        self,
        *,
        text: str,
        timestamp: datetime | None = None,
        name: str | None = None,
    ):
        super().__init__(author="user", timestamp=timestamp)
        self.text = text
        self.name = name

    def get_content_for_user(self) -> str:
        return f"LLM Run Command Output: {self.text}"

    def get_content_for_assistant(self) -> str:
        return self.text

    def to_json(self) -> dict:
        return {
            "type": "llm_run_command_output",
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
        }

    @staticmethod
    def from_json(json_data: dict) -> "LLMRunCommandOutput":
        return LLMRunCommandOutput(
            text=json_data["text"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            name=json_data.get("name"),
        )