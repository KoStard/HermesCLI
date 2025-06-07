from typing import Any

from hermes.chat.interface.commands.command import Command as BaseCommand
from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl


class RewriteKnowledgeCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "rewrite_knowledge",
            "Rewrite the content of an existing knowledge entry.",
        )
        self.add_section("title", True, "Title of the knowledge entry to rewrite.")
        self.add_section("content", True, "New content to replace the existing content.")
        self.add_section("new_title", False, "Optional new title for the entry.")
        self.add_section(
            "tag",
            False,
            "Optional new tags for the entry (replaces all existing tags if specified).",
            allow_multiple=True,
        )

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Rewrite the content of an existing knowledge entry."""
        title = args["title"]
        content = args["content"]
        new_title = args.get("new_title")
        new_tags = args.get("tag")

        # Ensure tags is a list, even if only one is provided
        if isinstance(new_tags, str):
            new_tags = [new_tags]

        knowledge_base = context.research_project.get_knowledge_base()

        try:
            success = knowledge_base.update_entry(title, new_content=content, new_title=new_title, new_tags=new_tags)
            if success:
                title_msg = f" and title updated to '{new_title}'" if new_title else ""
                tags_msg = f" and tags updated to {new_tags}" if new_tags is not None else ""
                context.add_command_output(
                    self.name, args, f"Knowledge entry '{title}' content rewritten{title_msg}{tags_msg} successfully."
                )
            else:
                context.add_command_output(self.name, args, f"Error: Knowledge entry with title '{title}' not found.")
        except Exception as e:
            context.add_command_output(self.name, args, f"Error: {str(e)}")
