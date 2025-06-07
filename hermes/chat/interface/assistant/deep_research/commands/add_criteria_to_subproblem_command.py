from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research.research_node_component.criteria_manager import Criterion
from hermes.chat.interface.commands.command import Command as BaseCommand


class AddCriteriaToSubproblemCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "add_criteria_to_subproblem",
            "Add criteria to a subproblem",
        )
        self.add_section("title", True, "Title of the subproblem")
        self.add_section("criteria", True, "Criteria text")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Add criteria to a subproblem"""
        current_node = context.current_node

        # Get the subproblem by title
        title = args["title"]
        child_nodes = current_node.list_child_nodes()

        # Find the child node with matching title
        subproblem = None
        for child in child_nodes:
            if child.get_title() == title:
                subproblem = child
                break

        if not subproblem:
            return

        # Add criteria to the subproblem
        criteria_text = args["criteria"]
        existing_criteria = [c.content for c in subproblem.get_criteria()]
        if criteria_text in existing_criteria:
            return

        # Create and add criterion
        criterion = Criterion(content=criteria_text)
        subproblem.add_criterion(criterion)

        # Add confirmation output
        context.add_command_output(self.name, args, f"Criteria added to subproblem '{title}'.")
