"""
Events are what the engine sends to the participants.
It can contain a message, or just notification of something happening.
"""

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
import os
from hermes_beta.message import Message

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

"""
Notification events are events that contain a notification and are sent to the next participant.
"""

@dataclass(init=False)
class NotificationEvent(Event):
    text: str

    def __init__(self, text: str):
        self.text = text