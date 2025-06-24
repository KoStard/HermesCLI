"""Video command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import VideoMessage


def register() -> ControlPanelCommand:
    """Register the video command."""
    return ControlPanelCommand(
        command_id="video",
        command_label="/video",
        description="Add video to the conversation",
        short_description="Share a video file",
        parser=lambda line, control_panel: MessageEvent(VideoMessage(author="user", video_filepath=line)),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
