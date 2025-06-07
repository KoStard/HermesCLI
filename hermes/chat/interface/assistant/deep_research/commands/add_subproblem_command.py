from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.commands.command import Command as BaseCommand


class AddSubproblemCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "add_subproblem",
            "Add a subproblem to the current problem",
        )
        self.add_section("title", True, "Title of the subproblem")
        self.add_section("content", True, "Content of the subproblem definition")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Add a subproblem to the current problem"""
        current_node = context.current_node

        # Check if subproblem with this title already exists
        title = args["title"]
        for child in current_node.list_child_nodes():
            if child.get_title() == title:
                return

        # Create the child node using the encapsulated method
        current_node.create_child_node(title=title, problem_content=args["content"])

        # Add confirmation output
        context.add_command_output(self.name, args, f"Subproblem '{title}' added.")
