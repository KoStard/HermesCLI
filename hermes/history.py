"""
History keeps track of the messages in the conversation.
"""

import json
from asyncio import Event
from typing import List

from hermes_beta.event import MessageEvent
from hermes_beta.message import Message, DESERIALIZATION_KEYMAP


class History:
    messages: List[Message]
    def __init__(self):
        self.messages = []

    def add_message(self, message: Message):
        self.messages.append(message)

    def get_messages(self) -> List[Message]:
        return self.messages[:]
    
    def get_messages_as_events(self) -> List[Event]:
        return [MessageEvent(message) for message in self.messages]

    def clear(self):
        self.messages = []
    
    def save(self, filename: str):
        """
        Save the conversation history to a JSON file.
        
        Args:
            filename (str): Path to the file where history should be saved
        """
        history_data = {
            "messages": [
                {
                    **message.to_json(),
                }
                for message in self.messages
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
            self.add_message(message)