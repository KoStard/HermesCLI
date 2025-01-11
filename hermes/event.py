"""
Events are what the engine sends to the participants.
It can contain a message, or just notification of something happening.
"""

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
import os
from hermes.message import Message, TextGeneratorMessage, TextMessage, ThinkingAndResponseGeneratorMessage

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
class AgentModeEvent(EngineCommandEvent):
    enabled: bool

@dataclass
class FileEditEvent(EngineCommandEvent):
    """Event for file operations like create, append or update markdown sections"""
    file_path: str
    content: str
    mode: str  # 'create', 'append', 'update_markdown_section', 'append_markdown_section'
    submode: str = None  # Optional, only for specific use cases
    section_path: list[str] = None  # For markdown section updates, e.g. ['Introduction', 'Overview', '__preface']


@dataclass
class AssistantDoneEvent(EngineCommandEvent):
    """Event emitted when the assistant marks a task as done in agent mode"""

@dataclass
class LLMCommandsExecutionEvent(EngineCommandEvent):
    """Event for toggling LLM command execution"""
    enabled: bool

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
    content: TextMessage | TextGeneratorMessage | ThinkingAndResponseGeneratorMessage

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
        elif content_type == "thinking_and_response_generator":
            return RawContentForHistoryEvent(content=ThinkingAndResponseGeneratorMessage.from_json(json_data["content"]))
        else:
            raise ValueError(f"Unknown content type: {content_type}")
