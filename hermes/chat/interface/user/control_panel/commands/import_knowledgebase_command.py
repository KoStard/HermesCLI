"""Import knowledgebase command for the user control panel."""

from pathlib import Path

from hermes.chat.events.engine_commands.import_knowledgebase import ImportKnowledgebaseEvent
from hermes.chat.interface.control_panel import ControlPanelCommand


def register() -> ControlPanelCommand:
    """Register the import knowledgebase command."""
    return ControlPanelCommand(
        command_id="import_knowledgebase",
        command_label="/import_knowledgebase",
        description="Import knowledgebase from a directory (pass the knowledgebase directory, not the research)",
        short_description="Import knowledgebase",
        parser=lambda line: ImportKnowledgebaseEvent(knowledgebase_path=Path(line)),
        is_research_command=True,
        is_chat_command=False,
        is_agent_command=False,
    )
