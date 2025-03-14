"""
History keeps track of the messages in the conversation.
"""

import json
from asyncio import Event
from dataclasses import dataclass
from typing import List

from hermes.event import MessageEvent, RawContentForHistoryEvent
from hermes.message import (
    Message,
    DESERIALIZATION_KEYMAP,
    TextGeneratorMessage,
    TextMessage,
    ThinkingAndResponseGeneratorMessage,
)


@dataclass
class HistoryItem:
    """Wrapper for messages in history with additional metadata"""

    message: Message | None = None
    raw_content: RawContentForHistoryEvent | None = None

    def to_json(self) -> dict:
        return {
            "message": self.message.to_json() if self.message else None,
            "raw_content": self.raw_content.to_json() if self.raw_content else None,
        }

    @staticmethod
    def from_json(history_item: dict):
        if "message" not in history_item and "raw_content" not in history_item:
            print(
                "Missing 'message' or 'raw_content' key in history data, skipping:",
                history_item,
            )
            return

        if history_item.get("message"):
            message_data = history_item["message"]
            message_type = message_data["type"]
            if message_type not in DESERIALIZATION_KEYMAP:
                raise ValueError(f"Unknown message type: {message_type}")

            message = DESERIALIZATION_KEYMAP[message_type](message_data)
            return HistoryItem(message=message)
        else:
            raw_content = RawContentForHistoryEvent.from_json(
                history_item["raw_content"]
            )
            return HistoryItem(raw_content=raw_content)


class History:
    _committed_items: List[HistoryItem]
    _uncommitted_items: List[HistoryItem]

    def __init__(self):
        self._committed_items = []
        self._uncommitted_items = []

    def add_message(self, message: Message):
        self._uncommitted_items.append(HistoryItem(message=message))

    def add_raw_content(self, raw_content: RawContentForHistoryEvent):
        self._uncommitted_items.append(HistoryItem(raw_content=raw_content))

    def commit(self):
        """Move uncommitted items to committed"""
        self._committed_items.extend(self._uncommitted_items)
        self._uncommitted_items = []

    def reset_uncommitted(self):
        """Clear uncommitted items without committing"""
        had_changes = bool(self._uncommitted_items)
        self._uncommitted_items = []
        return had_changes

    def get_messages(self) -> List[Message]:
        all_items = self._committed_items + self._uncommitted_items
        return [item.message for item in all_items if item.message]

    def get_messages_as_events(self) -> List[Event]:
        all_items = self._committed_items + self._uncommitted_items
        return [MessageEvent(item.message) for item in all_items if item.message]

    def get_history_for(self, author: str) -> List[Message]:
        results = []
        all_items = self._committed_items + self._uncommitted_items
        for item in all_items:
            # Not including the text that is directly entered, which means is directly extracted from the raw content, which is included as well
            if item.message:
                if item.message.author != author:
                    results.append(item.message)
                elif item.message.author == author:
                    if (
                        hasattr(item.message, "is_directly_entered")
                        and item.message.is_directly_entered
                    ):
                        continue
                    results.append(item.message)
            elif item.raw_content and item.raw_content.content.author == author:
                results.append(item.raw_content.content)
        return results

    def clear(self):
        self._committed_items = []
        self._uncommitted_items = []

    def save(self, filename: str):
        """
        Save the conversation history to a JSON file.

        Args:
            filename (str): Path to the file where history should be saved
        """
        history_data = {"messages": [item.to_json() for item in self._committed_items]}

        with open(filename, "w", encoding="utf-8") as f:
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
        with open(filename, "r", encoding="utf-8") as f:
            history_data = json.load(f)

        self.clear()

        for history_item in history_data["messages"]:
            self._committed_items.append(HistoryItem.from_json(history_item))
