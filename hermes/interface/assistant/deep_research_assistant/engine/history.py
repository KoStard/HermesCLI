from typing import List, Optional


class ChatMessage:
    """Represents a single message in the chat history"""

    def __init__(self, author: str, content: str):
        self.author = author
        self.content = content


class ChatHistory:
    """Manages the chat history for the current focus level"""

    def __init__(self):
        self.messages: List[ChatMessage] = []

    def add_message(self, author: str, content: str) -> None:
        """Add a message to the history"""
        self.messages.append(ChatMessage(author, content))

    def clear(self) -> None:
        """Clear all messages from history"""
        self.messages.clear()
