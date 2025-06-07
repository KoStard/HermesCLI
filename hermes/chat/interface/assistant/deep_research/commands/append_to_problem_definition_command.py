from typing import Any

from hermes.chat.interface.commands.command import Command as BaseCommand
from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl


class AppendToProblemDefinitionCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "append_to_problem_definition",
            "Append content to the current problem definition",
        )
        self.add_section("content", True, "Content to append")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Append to the problem definition"""
        current_node = context.current_node

        current_node.append_to_problem_definition(args["content"])

        # Add confirmation output
        context.add_command_output(self.name, args, "Problem definition updated.")
