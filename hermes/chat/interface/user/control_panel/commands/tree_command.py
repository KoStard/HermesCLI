"""Tree command for the user control panel."""

import os
import shlex

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.messages import TextualFileMessage
from hermes.utils.file_extension import remove_quotes


def _parse_tree_command(control_panel, content: str) -> MessageEvent:
    """Parse the /tree command and generate a directory tree.

    Args:
        content: The command content after the label

    Returns:
        MessageEvent with the tree structure
    """
    # Handle quoted paths with spaces
    parts = shlex.split(content)

    path = os.getcwd() if not parts else remove_quotes(parts[0])
    depth = int(parts[1]) if len(parts) > 1 else None

    tree_string = control_panel.tree_generator.generate_tree(path, depth)
    tree_message = TextualFileMessage(
        author="user",
        textual_content=tree_string,
        text_filepath=None,
        file_role="tree_result",
    )
    return MessageEvent(tree_message)


def register() -> ControlPanelCommand:
    """Register the tree command."""
    return ControlPanelCommand(
        command_id="tree",
        command_label="/tree",
        description="Generate a directory tree",
        short_description="Show directory structure",
        parser=lambda line, control_panel: _parse_tree_command(control_panel, line),
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=True,
    )
