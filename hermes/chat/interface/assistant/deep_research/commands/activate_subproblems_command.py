import textwrap
from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.commands.command import Command


class ActivateSubproblems(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "activate_subproblems",
            textwrap.dedent("""
            Activate subproblems to run in parallel. Multiple titles can be specified.
            Can be executed on subproblems that previously have been executed as well.
            """),
        )
        self.add_section("title", True, "Title of the subproblem to activate", allow_multiple=True)

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Activate subproblems for parallel execution"""
        titles = self._normalize_titles(args["title"])
        self._validate_titles_exist(titles, context)
        self._activate_all_subproblems(titles, context)
        self._add_success_output(titles, context, args)

    def _normalize_titles(self, titles_input: Any) -> list[str]:
        """Convert titles input to list format"""
        titles = titles_input if isinstance(titles_input, list) else [titles_input]
        if not titles:
            raise ValueError("No subproblems specified to activate")
        return titles

    def _validate_titles_exist(self, titles: list[str], context: ResearchCommandContextImpl) -> None:
        """Validate that all specified subproblems exist"""
        child_node_titles = {node.get_title() for node in context.current_node.list_child_nodes()}
        for title in titles:
            if title not in child_node_titles:
                raise ValueError(f"Subproblem '{title}' not found")

    def _activate_all_subproblems(self, titles: list[str], context: ResearchCommandContextImpl) -> None:
        """Activate each subproblem without waiting"""
        for title in titles:
            result = context.activate_subtask(title)
            if not result:
                raise ValueError(f"Failed to activate subproblem '{title}'")

    def _add_success_output(self, titles: list[str], context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Add command success output"""
        context.add_command_output(
            self.name,
            args,
            f"Activated subproblems for parallel execution: {', '.join(titles)}.",
        )
