"""Command modules for the user control panel.

Example:
from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import TextualFileMessage


def register() -> ControlPanelCommand:
    return ControlPanelCommand(
        command_id="textual_file",
        command_label="/textual_file",
        description="Add text file to the conversation. Supported: plain textual files, PDFs, DOCs, PowerPoint, Excel, etc.",
        short_description="Share a text-based document",
        parser=lambda line, control_panel: MessageEvent(TextualFileMessage(author="user", text_filepath=line, textual_content=None)),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=True,
    )

"""
