from abc import ABC
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from hermes.interface.assistant.deep_research_assistant.engine.content_truncator import ContentTruncator


class HistoryBlock(ABC):
    pass


class ChatMessage(HistoryBlock):
    """Represents a single message in the chat history"""

    def __init__(self, author: str, content: str):
        self.author = author
        self.content = content


class AutoReply(HistoryBlock):
    def __init__(self, error_report: str, command_outputs: List[Tuple[str, dict]]):
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
            for cmd_name, output_data in self.command_outputs:
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


class AutoReplyAggregator:
    def __init__(self):
        self.error_reports = []
        self.command_outputs = []

    def add_error_report(self, error_report: str):
        self.error_reports.append(error_report)

    def add_command_output(self, cmd_name: str, output_data: dict):
        self.command_outputs.append((cmd_name, output_data))

    def clear(self):
        self.error_reports = []
        self.command_outputs = []

    def is_empty(self):
        return not self.error_reports and not self.command_outputs

    def compile_and_clear(self) -> AutoReply:
        error_report = "\n".join(self.error_reports)
        auto_reply = AutoReply(error_report, self.command_outputs)
        self.clear()
        return auto_reply


class ChatHistory:
    """Manages the chat history for all nodes in the problem hierarchy"""

    def __init__(self):
        # Map of node_title -> list of messages
        self.node_blocks: Dict[str, List[HistoryBlock]] = defaultdict(list)
        self.node_auto_reply_aggregators: Dict[str, AutoReplyAggregator] = defaultdict(AutoReplyAggregator)

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

    def commit_and_get_blocks(self, node_title: str) -> List[HistoryBlock]:
        """Get all history blocks for a specific node"""
        auto_reply_aggregator = self.node_auto_reply_aggregators[node_title]
        if not auto_reply_aggregator.is_empty():
            auto_reply = auto_reply_aggregator.compile_and_clear()
            self.node_blocks[node_title].append(auto_reply)
        return self.node_blocks[node_title]
