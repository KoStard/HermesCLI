"""Text command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import TextMessage


def register() -> ControlPanelCommand:
    """Register the text command."""
    return ControlPanelCommand(
        command_id="text",
        command_label="/text",
        description="Add text to the conversation",
        short_description="Send a text message",
        parser=lambda line: MessageEvent(TextMessage(author="user", text=line, is_directly_entered=True)),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=True,
    )
