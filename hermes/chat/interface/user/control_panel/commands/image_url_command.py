"""Image URL command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import ImageUrlMessage


def register() -> ControlPanelCommand:
    """Register the image URL command."""
    return ControlPanelCommand(
        command_id="image_url",
        command_label="/image_url",
        description="Add image from url to the conversation",
        short_description="Share an image via URL",
        parser=lambda line: MessageEvent(ImageUrlMessage(author="user", image_url=line)),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
