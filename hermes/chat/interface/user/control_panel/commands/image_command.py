"""Image command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import ImageMessage


def register() -> ControlPanelCommand:
    """Register the image command."""
    return ControlPanelCommand(
        command_id="image",
        command_label="/image",
        description="Add image to the conversation",
        short_description="Share an image file",
        parser=lambda line, control_panel: MessageEvent(ImageMessage(author="user", image_path=line)),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
