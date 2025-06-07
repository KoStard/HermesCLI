from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research import ProblemStatus
from hermes.chat.interface.commands.command import Command as BaseCommand


class WaitForSubproblems(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "wait_for_subproblems",
            "Wait for specific subproblems to complete before continuing.",
        )
        self.add_section("title", True, "Title of the subproblem to wait for", allow_multiple=True)

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Wait for specified subproblems to complete"""
        titles = args["title"]
        if not isinstance(titles, list):
            titles = [titles]

        if not titles:
            raise ValueError("No subproblems specified to wait for")

        current_node = context.current_node
        child_nodes = current_node.list_child_nodes()
        active_titles = {
            node.get_title()
            for node in child_nodes
            if node.get_problem_status() not in {ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.CANCELLED}
        }

        # Validate all specified subproblems exist and are active
        for title in titles:
            if title not in active_titles:
                raise ValueError(f"Subproblem '{title}' not found or not active")

        for title in titles:
            context.wait_for_subtask(title)

        context.add_command_output(
            self.name,
            args,
            f"Waiting for subproblems to complete: {', '.join(titles)}.",
        )
