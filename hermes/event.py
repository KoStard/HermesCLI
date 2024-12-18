"""
Events are what the engine sends to the participants.
It can contain a message, or just notification of something happening.
"""

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
import os
from hermes.message import Message, TextGeneratorMessage, TextMessage

@dataclass(init=False)
class Event(ABC):
    pass


"""
Message events are events that contain a message and are sent to the next participant.
"""

@dataclass(init=False)
class MessageEvent(Event):
    message: Message

    def __init__(self, message: Message):
        self.message = message

    def get_message(self) -> Message:
        return self.message

"""
Engine commands are commands that the engine can execute.
"""

@dataclass(init=False)
class EngineCommandEvent(Event):
    pass

@dataclass(init=False)
class ClearHistoryEvent(EngineCommandEvent):
    pass

@dataclass(init=False)
class SaveHistoryEvent(EngineCommandEvent):
    filepath: str

    def __init__(self, filepath: str = ""):
        filepath = filepath.strip()
        if not filepath:
            filepath = self._get_default_filepath()
        self.filepath = filepath

    def _get_default_filepath(self) -> str:
        return f"hermes_history_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

@dataclass(init=False)
class LoadHistoryEvent(EngineCommandEvent):
    filepath: str

    def __init__(self, filepath: str):
        filepath = filepath.strip()
        self.filepath = self._verify_filepath(filepath)
    
    def _verify_filepath(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            raise ValueError(f"Filepath {filepath} does not exist")
        return filepath

@dataclass(init=False)
class ExitEvent(EngineCommandEvent):
    pass

@dataclass
class FileEditEvent(EngineCommandEvent):
    """Event for file operations like create or append"""
    file_path: str
    content: str
    mode: str  # 'create' or 'append'

@dataclass
class UpdateLLMToolchain(EngineCommandEvent):
    """Event to update the LLM toolchain with a list of enabled tools."""
    enabled_tools: list[str]

    def __init__(self, tools: str):
        self.enabled_tools = [tool.strip() for tool in tools.split(",")]
        self._validate_tools()

    def _validate_tools(self):
        valid_tools = []  # Hardcoded list of valid tools, currently empty
        invalid_tools = [tool for tool in self.enabled_tools if tool not in valid_tools]
        if invalid_tools:
            raise ValueError(f"Invalid tools provided: {', '.join(invalid_tools)}")

"""
Notification events are events that contain a notification and are sent to the next participant.
"""

@dataclass(init=False)
class NotificationEvent(Event):
    text: str

    def __init__(self, text: str):
        self.text = text


@dataclass
class RawContentForHistoryEvent(Event):
    content: TextMessage | TextGeneratorMessage

    def to_json(self) -> dict:
        return {
            "type": "raw_content",
            "content": self.content.to_json()
        }
    
    @staticmethod
    def from_json(json_data: dict) -> "RawContentForHistoryEvent":
        content_type = json_data["content"]["type"]
        if content_type == "text":
            return RawContentForHistoryEvent(content=TextMessage.from_json(json_data["content"]))
        elif content_type == "text_generator":
            return RawContentForHistoryEvent(content=TextGeneratorMessage.from_json(json_data["content"]))
        else:
            raise ValueError(f"Unknown content type: {content_type}")
