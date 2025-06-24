"""URL command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import UrlMessage


def register() -> ControlPanelCommand:
    """Register the url command."""
    return ControlPanelCommand(
        command_id="url",
        command_label="/url",
        description="Add url to the conversation",
        short_description="Share a URL",
        parser=lambda line: MessageEvent(UrlMessage(author="user", url=line)),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
