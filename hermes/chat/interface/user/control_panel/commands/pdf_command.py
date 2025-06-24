"""PDF command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import EmbeddedPDFMessage


def register() -> ControlPanelCommand:
    """Register the pdf command."""
    return ControlPanelCommand(
        command_id="pdf",
        command_label="/pdf",
        description="Add pdf to the conversation. After the PDF path, optionally use "
        "{<page_number>, <page_number>:<page_number>, ...} to specify pages.",
        short_description="Share a PDF file",
        parser=lambda line, control_panel: MessageEvent(EmbeddedPDFMessage.build_from_line(author="user", raw_line=line)),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
