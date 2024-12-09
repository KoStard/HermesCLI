"""
History keeps track of the messages in the conversation.
"""

import json
from asyncio import Event
from dataclasses import dataclass
from typing import List

from hermes.event import MessageEvent
from hermes.message import Message, DESERIALIZATION_KEYMAP


@dataclass
class HistoryItem:
    """Wrapper for messages in history with additional metadata"""
    message: Message
    # Add additional fields here as needed, e.g.:
    # timestamp: datetime
    # metadata: dict

    def to_json(self) -> dict:
        return {
            **self.message.to_json(),
            # Add serialization for additional fields here
        }


class History:
    _items: List[HistoryItem]
    def __init__(self):
        self._items = []

    def add_message(self, message: Message):
        self._items.append(HistoryItem(message=message))

    def get_messages(self) -> List[Message]:
        return [item.message for item in self._items]
    
    def get_messages_as_events(self) -> List[Event]:
        return [MessageEvent(item.message) for item in self._items]

    def clear(self):
        self._items = []
    
    def save(self, filename: str):
        """
        Save the conversation history to a JSON file.
        
        Args:
            filename (str): Path to the file where history should be saved
        """
        history_data = {
            "messages": [
                item.to_json()
                for item in self._items
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)

    def load(self, filename: str):
        """
        Load conversation history from a JSON file.
        
        Args:
            filename (str): Path to the file containing saved history
            
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            KeyError: If the file is missing required message data
            ValueError: If message type is not recognized
        """
        with open(filename, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        self.clear()
        
        for message_data in history_data["messages"]:
            message_type = message_data["type"]
            if message_type not in DESERIALIZATION_KEYMAP:
                raise ValueError(f"Unknown message type: {message_type}")
            
            message = DESERIALIZATION_KEYMAP[message_type](message_data)
            self._items.append(HistoryItem(message=message))
