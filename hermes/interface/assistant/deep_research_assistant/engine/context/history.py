import traceback
from collections import defaultdict

from hermes.interface.assistant.deep_research_assistant.engine.context.content_truncator import (
    ContentTruncator,
)
from hermes.interface.templates.template_manager import TemplateManager

from .dynamic_sections import RendererRegistry  # Use the type alias

# Import base data class from its new location
from .dynamic_sections.base import DynamicSectionData


class HistoryBlock:
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
        command_outputs: list[tuple[str, dict]],
        messages: list[tuple[str, str]],
        confirmation_request: str | None = None,
        dynamic_sections: list[tuple[int, DynamicSectionData]] | None = None,
    ):
        self.error_report: str = error_report
        self.command_outputs: list[tuple[str, dict]] = command_outputs
        self.messages: list[tuple[str, str]] = messages
        self.confirmation_request: str | None = confirmation_request
        # Store the data objects, not rendered strings
        self.dynamic_sections: list[tuple[int, DynamicSectionData]] = dynamic_sections or []

    def generate_auto_reply(
        self,
        template_manager: TemplateManager,
        renderer_registry: RendererRegistry,
        future_changes_map: dict[int, int],
        per_command_output_maximum_length: int | None = None,
    ) -> str:
        """
        Generate an automatic reply using a Mako template, rendering dynamic sections on the fly.

        Args:
            template_manager: The template manager instance.
            renderer_registry: Maps data types to renderer instances.
            future_changes_map: Maps section index to its future change count.
            per_command_output_maximum_length: Optional max length for command outputs.

        Returns:
            Formatted automatic reply string.
        """
        # --- Render Dynamic Sections ---
        rendered_dynamic_sections: list[tuple[int, str]] = []
        for index, data_instance in self.dynamic_sections:
            data_type = type(data_instance)
            renderer = renderer_registry.get(data_type)
            future_changes = future_changes_map.get(index, 0)
            rendered_content = ""

            if renderer:
                try:
                    # Pass future_changes count to the renderer
                    rendered_content = renderer.render(data_instance, future_changes)
                except Exception:
                    # Error handling as requested: print stack trace and generate message
                    print(f"\n--- ERROR RENDERING DYNAMIC SECTION (Index: {index}, Type: {data_type.__name__}) ---")
                    tb_str = traceback.format_exc()
                    print(tb_str)
                    print("--- END ERROR ---")
                    # Corrected f-string for artifact name
                    artifact_name = f"render_error_section_{index}_{data_type.__name__}"
                    rendered_content = (
                        f'<error context="Rendering dynamic section index {index} ({data_type.__name__})">\n'
                        f"**SYSTEM ERROR:** Failed to render this section. "
                        f"Please create an artifact named '{artifact_name}' "
                        f"with the following content:\n```\n{tb_str}\n```\n"
                        "Then, inform the administrator.\n"
                        "</error>"
                    )
            else:
                # Handle case where renderer is missing (shouldn't happen with proper registry)
                print(f"Warning: No renderer found for dynamic section type {data_type.__name__}")
                rendered_content = f"<error>No renderer found for section type {data_type.__name__}</error>"

            rendered_dynamic_sections.append((index, rendered_content))

        # --- Prepare Context for Mako Template ---
        context = {
            "confirmation_request": self.confirmation_request,
            "error_report": self.error_report,
            "command_outputs": self.command_outputs,
            "messages": self.messages,
            "rendered_dynamic_sections": rendered_dynamic_sections,  # Pass rendered strings
            "per_command_output_maximum_length": per_command_output_maximum_length,
            "ContentTruncator": ContentTruncator,  # Still needed for command output truncation
        }

        # --- Render the Main Auto-Reply Template ---
        try:
            return template_manager.render_template("context/auto_reply.mako", **context)
        except Exception:
            # Handle potential errors in the main auto_reply.mako template itself
            print("\n--- ERROR RENDERING auto_reply.mako ---")
            tb_str = traceback.format_exc()
            print(tb_str)
            print("--- END ERROR ---")
            # Return a fallback error message if the main template fails
            return (
                f"# Automatic Reply\n\n"
                f"**SYSTEM ERROR:** Failed to render the main auto-reply structure.\n"
                f"Please report this error to the administrator.\n\n"
                f"Details:\n```\n{tb_str}\n```"
            )


class AutoReplyAggregator:
    def __init__(self):
        self.error_reports = []
        self.command_outputs = []
        self.internal_messages: list[tuple[str, str]] = []
        self.confirmation_requests: list[str] = []
        # Stores the *data* objects for changed sections and their original index
        self.dynamic_sections_to_report: list[tuple[int, DynamicSectionData]] = []
        # Stores the last known state of *all* dynamic section data objects
        self.last_dynamic_sections_state: list[DynamicSectionData] = []

    def add_error_report(self, error_report: str):
        self.error_reports.append(error_report)

    def add_confirmation_request(self, message: str):
        self.confirmation_requests.append(message)

    def add_command_output(self, cmd_name: str, output_data: dict):
        self.command_outputs.append((cmd_name, output_data))

    def add_internal_message_from(self, message: str, origin_node_title: str):
        self.internal_messages.append((message, origin_node_title))

    def update_dynamic_sections(self, new_sections_data: list[DynamicSectionData]):
        """
        Compare new dynamic section data with the last known state and track changes.

        Args:
            new_sections_data: List of data objects for all current dynamic sections.
        """
        changed_sections_with_indices: list[tuple[int, DynamicSectionData]] = []

        # Ensure lengths match for comparison, handle initialization
        if not self.last_dynamic_sections_state:
            # First time seeing sections, consider all as 'changed' for the initial view,
            # but don't report them in the *first* auto-reply unless explicitly needed.
            # For simplicity now, just initialize the state. The first auto-reply won't
            # list "updated sections" unless something else triggers it.
            self.last_dynamic_sections_state = new_sections_data[:]  # Use slicing for a copy
        elif len(new_sections_data) != len(self.last_dynamic_sections_state):
            # This indicates a structural change (sections added/removed), which
            # the current design doesn't handle dynamically. Treat all as changed.
            # Or log an error/warning. For now, assume fixed structure.
            print("Warning: Number of dynamic sections changed. Re-evaluating all.")
            for i, data_instance in enumerate(new_sections_data):
                # Check against old state if index exists, otherwise it's new/changed
                if i >= len(self.last_dynamic_sections_state) or data_instance != self.last_dynamic_sections_state[i]:
                    changed_sections_with_indices.append((i, data_instance))
        else:
            # Compare data objects element-wise using dataclass equality (__eq__)
            for i, current_data in enumerate(new_sections_data):
                if current_data != self.last_dynamic_sections_state[i]:
                    changed_sections_with_indices.append((i, current_data))

        # Store the changed sections (data + index) to be included in the *next* auto-reply
        self.dynamic_sections_to_report = changed_sections_with_indices

        # Update the last known state for *all* sections
        self.last_dynamic_sections_state = new_sections_data[:]  # Use slicing for a copy

    def clear(self):
        self.error_reports = []
        self.command_outputs = []
        self.internal_messages = []
        self.confirmation_requests = []
        self.dynamic_sections_to_report = []
        # Keep last_dynamic_sections_state for comparison

    def is_empty(self):
        """Check if there's anything to report in the auto-reply."""
        return (
            not self.error_reports
            and not self.command_outputs
            and not self.internal_messages
            and not self.confirmation_requests
            and not self.dynamic_sections_to_report  # Check the changed sections list
        )

    def compile_and_clear(self) -> AutoReply:
        error_report = "\n".join(self.error_reports)
        confirmation_request = "\n".join(self.confirmation_requests) if self.confirmation_requests else None
        auto_reply = AutoReply(
            error_report,
            self.command_outputs,
            self.internal_messages,
            confirmation_request,
            self.dynamic_sections_to_report,  # Pass the changed sections data
        )
        self.clear()  # Clears reports, outputs, messages, requests, and changed sections list
        return auto_reply


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
