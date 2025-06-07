from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.commands.command import Command as BaseCommand


class DeleteKnowledgeCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "delete_knowledge",
            "Delete an existing knowledge entry.",
        )
        self.add_section("title", True, "Title of the knowledge entry to delete.")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Delete an existing knowledge entry."""
        title = args["title"]

        knowledge_base = context.research_project.get_knowledge_base()

        success = knowledge_base.delete_entry(title)
        if success:
            context.add_command_output(self.name, args, f"Knowledge entry '{title}' deleted successfully.")
        else:
            context.add_command_output(self.name, args, f"Error: Knowledge entry with title '{title}' not found.")
