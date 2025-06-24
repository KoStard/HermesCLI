"""Textual files command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import TextualFileMessage


def register() -> ControlPanelCommand:
    """Register the textual files command."""
    return ControlPanelCommand(
        command_id="textual_files",
        command_label="/textual_files",
        description="Add text file to the conversation. Supported: plain textual files, PDFs, DOCs, PowerPoint, Excel, etc.",
        short_description="Share a text-based document",
        parser=lambda line: MessageEvent(TextualFileMessage(author="user", text_filepath=line, textual_content=None)),
        visible_from_interface=False,
        default_on_cli=True,
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=True,
    )
