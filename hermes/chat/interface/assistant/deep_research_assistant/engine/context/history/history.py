from collections import defaultdict

from hermes.chat.interface.assistant.deep_research_assistant.engine.context.history import HistoryBlock
from hermes.chat.interface.assistant.deep_research_assistant.engine.context.history.autoreply_aggregator import AutoReplyAggregator
from hermes.chat.interface.assistant.deep_research_assistant.engine.context.history.history_blocks import AutoReply, ChatMessage


class ChatHistory:
    """Manages the chat history for all nodes in the problem hierarchy"""

    def __init__(self):
        # Map of node_title -> list of messages
        self.node_blocks: dict[str, list[HistoryBlock]] = defaultdict(list)
        self.node_auto_reply_aggregators: dict[str, AutoReplyAggregator] = defaultdict(AutoReplyAggregator)

    def add_message(self, author: str, content: str, node_title: str) -> None:
        """Add a message to the current node's history"""
        message = ChatMessage(author, content)
        self.node_blocks[node_title].append(message)

    def get_auto_reply_aggregator(self, node_title: str) -> AutoReplyAggregator:
        """Add an automatic reply to the current node's history"""
        return self.node_auto_reply_aggregators[node_title]

    def clear_node_history(self, node_title: str) -> None:
        """Clear only the current node's history"""
        self.node_blocks[node_title] = []

    def commit_and_get_auto_reply(self, node_title: str) -> AutoReply | None:
        auto_reply_aggregator = self.node_auto_reply_aggregators[node_title]
        if not auto_reply_aggregator.is_empty() or len(self.node_blocks[node_title]) > 0:
            auto_reply = auto_reply_aggregator.compile_and_clear()
            self.node_blocks[node_title].append(auto_reply)
            return auto_reply
        return None

    def get_compiled_blocks(self, node_title: str) -> list[HistoryBlock]:
        """Get all history blocks for a specific node"""
        return self.node_blocks[node_title]
