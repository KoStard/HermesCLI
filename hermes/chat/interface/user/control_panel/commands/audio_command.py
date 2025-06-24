"""Audio command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import AudioFileMessage


def register() -> ControlPanelCommand:
    """Register the audio command."""
    return ControlPanelCommand(
        command_id="audio",
        command_label="/audio",
        description="Add audio to the conversation",
        short_description="Share an audio file",
        parser=lambda line, control_panel: MessageEvent(AudioFileMessage(author="user", audio_filepath=line)),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
