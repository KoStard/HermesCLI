"""History keeps track of the messages in the conversation."""

import json
from dataclasses import dataclass

from hermes.chat.events import Event, MessageEvent
from hermes.chat.messages import (
    DESERIALIZATION_KEYMAP,
    Message,
)


@dataclass
class HistoryItem:
    """Wrapper for messages in history with additional metadata"""

    message: Message | None = None

    def to_json(self) -> dict:
        return {
            "message": self.message.to_json() if self.message else None,
        }

    @staticmethod
    def from_json(history_item: dict):
        if "message" not in history_item:
            print(
                "Missing 'message' key in history data, skipping:",
                history_item,
            )
            return None

        message_data = history_item["message"]
        message_type = message_data["type"]
        if message_type not in DESERIALIZATION_KEYMAP:
            raise ValueError(f"Unknown message type: {message_type}")

        message = DESERIALIZATION_KEYMAP[message_type](message_data)
        return HistoryItem(message=message)


class History:
    _committed_items: list[HistoryItem]
    _uncommitted_items: list[HistoryItem]

    def __init__(self):
        self._committed_items = []
        self._uncommitted_items = []

    def add_message(self, message: Message):
        self._uncommitted_items.append(HistoryItem(message=message))

    def commit(self):
        """Move uncommitted items to committed"""
        self._committed_items.extend(self._uncommitted_items)
        self._uncommitted_items = []

    def reset_uncommitted(self):
        """Clear uncommitted items without committing"""
        had_changes = bool(self._uncommitted_items)
        self._uncommitted_items = []
        return had_changes

    def get_messages(self) -> list[Message]:
        all_items = self._committed_items + self._uncommitted_items
        return [item.message for item in all_items if item.message]

    def get_messages_as_events(self) -> list[Event]:
        all_items = self._committed_items + self._uncommitted_items
        return [MessageEvent(item.message) for item in all_items if item.message]

    def get_history_for(self, author: str) -> list[Message]:
        """Get history messages filtered for a specific author"""
        results = []
        all_items = self._get_all_history_items()

        for item in all_items:
            if self._should_include_in_history(item, author):
                results.append(item.message)

        return results

    def _get_all_history_items(self) -> list[HistoryItem]:
        """Get all history items, both committed and uncommitted"""
        return self._committed_items + self._uncommitted_items

    def _should_include_in_history(self, item: HistoryItem, author: str) -> bool:
        """Determine if history item should be included for the author"""
        # Ignore items without messages
        if not item.message:
            return False

        # For other authors, always include
        if item.message.author != author:
            return True

        # For messages from the target author, exclude directly entered ones
        return not (hasattr(item.message, "is_directly_entered") and item.message.is_directly_entered)

    def clear(self):
        self._committed_items = []
        self._uncommitted_items = []

    def save(self, filename: str):
        """Save the conversation history to a JSON file.

        Args:
            filename (str): Path to the file where history should be saved
        """
        history_data = {"messages": [item.to_json() for item in self._committed_items]}

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)

    def load(self, filename: str):
        """Load conversation history from a JSON file.

        Args:
            filename (str): Path to the file containing saved history

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            KeyError: If the file is missing required message data
            ValueError: If message type is not recognized
        """
        with open(filename, encoding="utf-8") as f:
            history_data = json.load(f)

        self.clear()

        for history_item in history_data["messages"]:
            self._committed_items.append(HistoryItem.from_json(history_item))
