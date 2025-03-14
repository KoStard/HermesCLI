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
    
    def get_formatted_history(self) -> str:
        """Get the formatted history as a string"""
        if not self.messages:
            return "No previous messages in this focus level."
        
        result = []
        for message in self.messages:
            result.append(f"## {message.author}")
            result.append(message.content)
            result.append("\n" + "-" * 50 + "\n")  # Separator between messages
        
        return "\n".join(result)
