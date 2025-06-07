from typing import Any

from hermes.chat.interface.commands.command import Command as BaseCommand
from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl


class AppendKnowledgeCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "append_knowledge",
            "Append content to an existing knowledge entry.",
        )
        self.add_section("title", True, "Title of the knowledge entry to append to.")
        self.add_section("content", True, "Content to append to the existing entry.")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Append content to an existing knowledge entry."""
        title = args["title"]
        content = args["content"]

        knowledge_base = context.research_project.get_knowledge_base()

        try:
            success = knowledge_base.append_content(title, append_content=content)
            if success:
                context.add_command_output(self.name, args, f"Content appended to knowledge entry '{title}' successfully.")
            else:
                context.add_command_output(self.name, args, f"Error: Knowledge entry with title '{title}' not found.")
        except Exception as e:
            context.add_command_output(self.name, args, f"Error: {str(e)}")
