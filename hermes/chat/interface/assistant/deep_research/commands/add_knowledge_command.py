from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research.research_project_component.knowledge_base import KnowledgeEntry
from hermes.chat.interface.commands.command import Command


class AddKnowledgeCommand(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "add_knowledge",
            "Add an entry to the shared knowledge base for all assistants.",
        )
        self.add_section("content", True, "The main content of the knowledge entry.")
        self.add_section("title", True, "Title for the entry (must be unique across all knowledge entries).")
        self.add_section(
            "tag",
            False,
            "Optional tag for categorization (can be used multiple times).",
            allow_multiple=True,
        )

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Add an entry to the shared knowledge base."""
        current_node = context.current_node

        tags = args.get("tag", [])
        # Ensure tags is a list, even if only one is provided
        if isinstance(tags, str):
            tags = [tags]

        try:
            entry = KnowledgeEntry(
                content=args["content"],
                author_node_title=current_node.get_title(),
                title=args["title"],
                tags=tags,
            )

            # Add the knowledge entry via the context
            context.add_knowledge_entry(entry)
            # Provide confirmation output using context
            context.add_command_output(self.name, args, f"Knowledge entry '{entry.title}' added successfully.")
        except ValueError as e:
            context.add_command_output(self.name, args, f"Error: {str(e)}")
