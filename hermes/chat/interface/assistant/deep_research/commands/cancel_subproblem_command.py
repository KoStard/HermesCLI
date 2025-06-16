from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research import ProblemStatus
from hermes.chat.interface.commands.command import Command


class CancelSubproblemCommand(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "cancel_subproblem",
            "Mark a subproblem as cancelled, if you no longer want to start it. It's a way to delete a subtask "
            "that you created but haven't yet started.",
        )
        self.add_section("title", True, "Title of the subproblem to cancel")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Cancel a subproblem"""
        current_node = context.current_node

        # Get the subproblem by title
        title = args["title"]
        child_nodes = current_node.list_child_nodes()

        # Find the child node with matching title
        target_child = None
        for child in child_nodes:
            if child.get_title() == title:
                target_child = child
                break

        if not target_child:
            raise ValueError(f"Subproblem '{title}' not found")

        # Mark the subproblem as cancelled
        target_child.set_problem_status(ProblemStatus.CANCELLED)

        # Add confirmation output
        context.add_command_output(self.name, args, f"Subproblem '{title}' cancelled.")
