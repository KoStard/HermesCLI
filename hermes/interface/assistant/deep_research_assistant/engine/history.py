from abc import ABC
from typing import Dict, List, Optional

from hermes.interface.assistant.deep_research_assistant.engine.content_truncator import ContentTruncator


class HistoryBlock(ABC):
    pass


class ChatMessage(HistoryBlock):
    """Represents a single message in the chat history"""

    def __init__(self, author: str, content: str):
        self.author = author
        self.content = content


class AutoReply(HistoryBlock):
    def __init__(self, error_report: str, command_outputs: Dict[str, List[Dict[str, any]]]):
        self.error_report = error_report
        self.command_outputs = command_outputs

    def generate_auto_reply(self, per_command_output_maximum_length: int = None) -> str:
        """
        Generate an automatic reply based on command execution results

        Args:

        Returns:
            Formatted automatic reply string
        """
        auto_reply = f'Automatic Reply: The status of the research is "In Progress". Please continue the research or mark it as done using `focus_up` command.'

        # Add error report if any
        if self.error_report:
            auto_reply += f"\n\n{self.error_report}"

        # Add command outputs if any
        if self.command_outputs:
            auto_reply += "\n\n### Command Outputs\n"
            for cmd_name, outputs in self.command_outputs.items():
                for output_data in outputs:
                    auto_reply += f"\n#### <<< {cmd_name}\n"
                    # Format arguments
                    args_str = ", ".join(
                        f"{k}: {v}" for k, v in output_data["args"].items()
                    )
                    if args_str:
                        auto_reply += f"Arguments: {args_str}\n\n"
                    # Add the output
                    if not per_command_output_maximum_length:
                        truncated_output = output_data['output']
                    else:
                        truncated_output = ContentTruncator.truncate(output_data['output'], per_command_output_maximum_length, additional_help="To see the full content again, rerun the command.")
                    auto_reply += f"```\n{truncated_output}\n```\n"

        return auto_reply


class ChatHistory:
    """Manages the chat history for all nodes in the problem hierarchy"""

    def __init__(self):
        # Map of node_id -> list of messages
        self.node_blocks: Dict[str, List[HistoryBlock]] = {}
        # Current active node ID
        self.current_node_id: Optional[str] = None
        # Current active messages list (points to the current node's messages)
        self.blocks: List[HistoryBlock] = []

    def set_current_node(self, node_id: str) -> None:
        """Set the current node and load its history"""
        self.current_node_id = node_id

        # Initialize history for this node if it doesn't exist
        if node_id not in self.node_blocks:
            self.node_blocks[node_id] = []

        # Point messages to the current node's history
        self.blocks = self.node_blocks[node_id]

    def add_message(self, author: str, content: str) -> None:
        """Add a message to the current node's history"""
        if not self.current_node_id:
            # If no current node is set, we can't add messages
            return

        message = ChatMessage(author, content)
        self.blocks.append(message)

    def add_auto_reply(self, auto_reply: AutoReply) -> None:
        """Add an automatic reply to the current node's history"""
        if not self.current_node_id:
            # If no current node is set, we can't add messages
            return

        self.blocks.append(auto_reply)

    def clear(self) -> None:
        """Clear all messages from all histories"""
        self.node_blocks.clear()
        self.current_node_id = None
        self.blocks = []

    def clear_current_node_history(self) -> None:
        """Clear only the current node's history"""
        if self.current_node_id:
            self.node_blocks[self.current_node_id] = []
            self.blocks = []
