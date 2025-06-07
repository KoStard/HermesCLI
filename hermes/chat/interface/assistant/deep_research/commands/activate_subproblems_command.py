from typing import Any

from hermes.chat.interface.commands.command import Command as BaseCommand
from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl


class ActivateSubproblems(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "activate_subproblems",
            "Activate subproblems to run in parallel. Multiple titles can be specified.",
        )
        self.add_section("title", True, "Title of the subproblem to activate", allow_multiple=True)

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Activate subproblems for parallel execution"""
        titles = args["title"]
        if not isinstance(titles, list):
            titles = [titles]

        if not titles:
            raise ValueError("No subproblems specified to activate")

        current_node = context.current_node
        child_node_titles = {node.get_title() for node in current_node.list_child_nodes()}

        # Validate and queue subproblems for parallel activation
        for title in titles:
            if title not in child_node_titles:
                raise ValueError(f"Subproblem '{title}' not found")

        for title in titles:
            # Activate each subproblem without waiting
            result = context.activate_subtask(title)
            if not result:
                raise ValueError(f"Failed to activate subproblem '{title}'")

        context.add_command_output(
            self.name,
            args,
            f"Activated subproblems for parallel execution: {', '.join(titles)}.",
        )
