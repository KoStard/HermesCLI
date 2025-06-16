from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research import ProblemStatus
from hermes.chat.interface.commands.command import Command


class WaitForSubproblems(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "wait_for_subproblems",
            "Wait for specific subproblems to complete before continuing.",
        )
        self.add_section("title", True, "Title of the subproblem to wait for", allow_multiple=True)

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Wait for specified subproblems to complete"""
        titles = self._normalize_titles(args["title"])
        active_titles = self._get_active_subproblem_titles(context)
        self._validate_titles_are_active(titles, active_titles)
        self._wait_for_all_subproblems(titles, context)
        self._add_success_output(titles, context, args)

    def _normalize_titles(self, titles_input: Any) -> list[str]:
        """Convert titles input to list format"""
        titles = titles_input if isinstance(titles_input, list) else [titles_input]
        if not titles:
            raise ValueError("No subproblems specified to wait for")
        return titles

    def _get_active_subproblem_titles(self, context: ResearchCommandContextImpl) -> set[str]:
        """Get titles of all active subproblems"""
        child_nodes = context.current_node.list_child_nodes()
        return {
            node.get_title()
            for node in child_nodes
            if node.get_problem_status() not in {ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.CANCELLED}
        }

    def _validate_titles_are_active(self, titles: list[str], active_titles: set[str]) -> None:
        """Validate all specified subproblems exist and are active"""
        for title in titles:
            if title not in active_titles:
                raise ValueError(f"Subproblem '{title}' not found or not active")

    def _wait_for_all_subproblems(self, titles: list[str], context: ResearchCommandContextImpl) -> None:
        """Wait for each specified subproblem"""
        for title in titles:
            context.wait_for_subtask(title)

    def _add_success_output(self, titles: list[str], context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Add command success output"""
        context.add_command_output(
            self.name,
            args,
            f"Waiting for subproblems to complete: {', '.join(titles)}.",
        )
