
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.history.autoreply_aggregator import (
    AutoReplyAggregator,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.history.history_blocks import (
    AutoReply,
    ChatMessage,
)


class ResearchNodeHistory:
    """Manages the chat history for a research node"""

    def __init__(self):
        self._compiled_blocks = []
        self._auto_reply_aggregator = AutoReplyAggregator()

    def add_message(self, author: str, content: str) -> None:
        """Add a message to the history"""
        self._compiled_blocks.append(ChatMessage(author=author, content=content))

    def get_compiled_blocks(self) -> list:
        """Get all blocks in the history"""
        return self._compiled_blocks.copy()

    def get_auto_reply_aggregator(self) -> AutoReplyAggregator:
        """Get the auto-reply aggregator for this history"""
        return self._auto_reply_aggregator

    def commit_and_get_auto_reply(self) -> AutoReply | None:
        """Commit the current auto-reply and return it"""
        # Skip if nothing to commit
        if self._auto_reply_aggregator.is_empty():
            return None

        # Create the auto-reply block
        auto_reply = self._auto_reply_aggregator.compile_and_clear()

        # Add to history
        self._compiled_blocks.append(auto_reply)

        return auto_reply
