from typing import Dict, List, Optional


class ChatMessage:
    """Represents a single message in the chat history"""

    def __init__(self, author: str, content: str):
        self.author = author
        self.content = content


class ChatHistory:
    """Manages the chat history for all nodes in the problem hierarchy"""

    def __init__(self):
        # Map of node_id -> list of messages
        self.node_histories: Dict[str, List[ChatMessage]] = {}
        # Current active node ID
        self.current_node_id: Optional[str] = None
        # Current active messages list (points to the current node's messages)
        self.messages: List[ChatMessage] = []

    def set_current_node(self, node_id: str) -> None:
        """Set the current node and load its history"""
        self.current_node_id = node_id

        # Initialize history for this node if it doesn't exist
        if node_id not in self.node_histories:
            self.node_histories[node_id] = []

        # Point messages to the current node's history
        self.messages = self.node_histories[node_id]

    def add_message(self, author: str, content: str) -> None:
        """Add a message to the current node's history"""
        if not self.current_node_id:
            # If no current node is set, we can't add messages
            return

        message = ChatMessage(author, content)
        self.messages.append(message)

        # Ensure the node_histories is updated (should be by reference, but being explicit)
        self.node_histories[self.current_node_id] = self.messages

    def clear(self) -> None:
        """Clear all messages from all histories"""
        self.node_histories.clear()
        self.current_node_id = None
        self.messages = []

    def clear_current_node_history(self) -> None:
        """Clear only the current node's history"""
        if self.current_node_id:
            self.node_histories[self.current_node_id] = []
            self.messages = []
