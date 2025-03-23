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
        # Map of node_title -> list of messages
        self.node_blocks: Dict[str, List[HistoryBlock]] = {}

    def add_message(self, author: str, content: str, node_title: str) -> None:
        """Add a message to the current node's history"""
        message = ChatMessage(author, content)
        if node_title not in self.node_blocks:
            self.node_blocks[node_title] = []
        self.node_blocks[node_title].append(message)

    def add_auto_reply(self, auto_reply: AutoReply, node_title: str) -> None:
        """Add an automatic reply to the current node's history"""
        if node_title not in self.node_blocks:
            self.node_blocks[node_title] = []
        self.node_blocks[node_title].append(auto_reply)

    def clear_node_history(self, node_title: str) -> None:
        """Clear only the current node's history"""
        self.node_blocks[node_title] = []

    def get_blocks(self, node_title: str) -> List[HistoryBlock]:
        """Get all history blocks for a specific node"""
        return self.node_blocks.get(node_title, [])
