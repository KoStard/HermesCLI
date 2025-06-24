"""Exa URL command for the user control panel."""

from datetime import datetime, timezone

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import TextualFileMessage


def _parse_exa_url_command(control_panel, raw_input: str) -> MessageEvent:
    """Parse and execute the /exa_url command"""
    if not control_panel.exa_client:
        raise ValueError("Exa integration not configured - missing EXA_API_KEY in config")

    url = raw_input.strip()
    result = control_panel.exa_client.get_contents(url)[0]

    result_text = result.text
    content_age = None
    if result.published_date:
        content_age = (datetime.now(timezone.utc) - datetime.fromisoformat(result.published_date).astimezone(timezone.utc)).days

    if not result_text:
        result_text = "WARNING: No content found"

    if content_age is None:
        result_text += "\n\n---\n\nWarning! No information available about the age of the content."
    elif content_age > 7:
        result_text += (
            f"\n\n---\n\nWarning! The snapshot of this website has been last updated {content_age} ago, "
            "it might not be fully up to date"
        )

    return MessageEvent(
        TextualFileMessage(
            author="user",
            name=result.title,
            text_filepath=None,
            file_role="url_content",
            textual_content=result_text,
        ),
    )


def register() -> ControlPanelCommand:
    """Register the exa url command."""
    return ControlPanelCommand(
        command_id="exa_url",
        command_label="/exa_url",
        description="Fetch and add content from a URL using Exa",
        short_description="Fetch URL content with Exa",
        parser=lambda line, control_panel=None: _parse_exa_url_command(control_panel, line),
        visible_from_cli=True,
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=False,
    )
