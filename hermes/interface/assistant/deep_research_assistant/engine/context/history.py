from abc import ABC
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from hermes.interface.assistant.deep_research_assistant.engine.context.content_truncator import ContentTruncator
from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import TemplateManager


class HistoryBlock(ABC):
    pass


class ChatMessage(HistoryBlock):
    """Represents a single message in the chat history"""

    def __init__(self, author: str, content: str):
        self.author = author
        self.content = content


class AutoReply(HistoryBlock):
    def __init__(
        self,
        error_report: str,
        command_outputs: List[Tuple[str, dict]],
        messages: List[Tuple[str, str]],
        confirmation_request: Optional[str] = None,
        dynamic_sections: Optional[List[Tuple[int, str]]] = None,
    ):
        self.error_report = error_report
        self.command_outputs = command_outputs
        self.messages = messages
        self.confirmation_request = confirmation_request
        self.dynamic_sections = dynamic_sections or []

    def generate_auto_reply(
        self,
        template_manager: TemplateManager,
        per_command_output_maximum_length: Optional[int] = None,
    ) -> str:
        """
        Generate an automatic reply based on command execution results using a Mako template.

        Args:
            template_manager: The template manager instance.
            per_command_output_maximum_length: Optional maximum length for command outputs.

        Returns:
            Formatted automatic reply string.

        Raises:
            Exception: If template rendering fails.
        """
        context = {
            "confirmation_request": self.confirmation_request,
            "error_report": self.error_report,
            "command_outputs": self.command_outputs,
            "messages": self.messages,
            "dynamic_sections": self.dynamic_sections,
            "per_command_output_maximum_length": per_command_output_maximum_length,
            "ContentTruncator": ContentTruncator,  # Pass the class itself
        }

        # Let exceptions propagate if rendering fails
        return template_manager.render_template("context/auto_reply.mako", **context)


class AutoReplyAggregator:
    def __init__(self):
        self.error_reports = []
        self.command_outputs = []
        self.internal_messages = []
        self.confirmation_requests = []
        self.dynamic_sections = []
        self.last_dynamic_sections = []

    def add_error_report(self, error_report: str):
        self.error_reports.append(error_report)

    def add_confirmation_request(self, message: str):
        self.confirmation_requests.append(message)

    def add_command_output(self, cmd_name: str, output_data: dict):
        self.command_outputs.append((cmd_name, output_data))

    def add_internal_message_from(self, message: str, origin_node_title: str):
        self.internal_messages.append((message, origin_node_title))

    def update_dynamic_sections(self, new_sections: List[str]):
        """
        Update tracked dynamic sections, identifying which ones have changed
        
        Args:
            new_sections: List of all current dynamic sections
        """
        changed_section_indices = []
        
        # Initialize last_dynamic_sections if empty
        if not self.last_dynamic_sections and new_sections:
            # If the last dynamic sections has not been initialized, not considering anything changed
            self.last_dynamic_sections = new_sections.copy()
        
        # Compare new sections with last known sections to find changes
        for i, content in enumerate(new_sections):
            if (i >= len(self.last_dynamic_sections) or 
                self.last_dynamic_sections[i] != content):
                changed_section_indices.append(i)
        
        # Store the changed sections to include in the next auto-reply
        self.dynamic_sections = [(i, new_sections[i]) for i in changed_section_indices]
        
        # Update last known state for all sections
        self.last_dynamic_sections = new_sections.copy()

    def clear(self):
        self.error_reports = []
        self.command_outputs = []
        self.internal_messages = []
        self.confirmation_requests = []
        self.dynamic_sections = []  # Keep last_dynamic_sections for comparison

    def is_empty(self):
        return (
            not self.error_reports
            and not self.command_outputs
            and not self.internal_messages
            and not self.confirmation_requests
            and not self.dynamic_sections
        )

    def compile_and_clear(self) -> AutoReply:
        error_report = "\n".join(self.error_reports)
        confirmation_request = (
            "\n".join(self.confirmation_requests)
            if self.confirmation_requests
            else None
        )
        auto_reply = AutoReply(
            error_report,
            self.command_outputs,
            self.internal_messages,
            confirmation_request,
            self.dynamic_sections,
        )
        self.clear()
        return auto_reply


class ChatHistory:
    """Manages the chat history for all nodes in the problem hierarchy"""

    def __init__(self):
        # Map of node_title -> list of messages
        self.node_blocks: Dict[str, List[HistoryBlock]] = defaultdict(list)
        self.node_auto_reply_aggregators: Dict[str, AutoReplyAggregator] = defaultdict(
            AutoReplyAggregator
        )

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

    def commit_and_get_auto_reply(self, node_title: str) -> Optional[AutoReply]:
        auto_reply_aggregator = self.node_auto_reply_aggregators[node_title]
        if not auto_reply_aggregator.is_empty() or len(self.node_blocks[node_title]) > 0:
            auto_reply = auto_reply_aggregator.compile_and_clear()
            self.node_blocks[node_title].append(auto_reply)
            return auto_reply
        return None

    def get_compiled_blocks(self, node_title: str) -> List[HistoryBlock]:
        """Get all history blocks for a specific node"""
        return self.node_blocks[node_title]
